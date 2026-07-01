"""
Endpoint de telemetría con persistencia (Fase 3).

Valida cada evento contra el contrato del esquema (envelope + payload whitelist),
persiste los válidos en Supabase y reporta los rechazados individualmente.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import ValidationError
from sqlalchemy import insert as sa_insert, select
from sqlmodel import Session

from ..core.database import get_sql_session
from ..schemas.telemetry import (
    TelemetryEvent,
)
from ..models import TelemetryEvent as TelemetryEventRecord

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.post("/events")
async def ingest_telemetry_events(
    batch: dict[str, Any],
    session: Session = Depends(get_sql_session),
) -> dict:
    """
    Recibe un lote de eventos de telemetría, valida y persiste.

    Cada evento se valida individualmente contra el contrato del esquema.
    Los eventos válidos se persisten en Supabase; los inválidos se rechazan
    individualmente pero el resto del lote se procesa igualmente.
    """
    raw_events = batch.get("events", [])
    if not isinstance(raw_events, list):
        raise ValueError("events must be a list")

    received = len(raw_events)
    rejected = 0
    valid_events: list[TelemetryEvent] = []
    duplicate_in_batch: set[str] = set()
    seen_event_ids: set[str] = set()

    for raw_event in raw_events:
        try:
            event = TelemetryEvent.model_validate(raw_event)
            _validate_event(event)
            if event.event_id in seen_event_ids:
                duplicate_in_batch.add(event.event_id)
                rejected += 1
                continue
            seen_event_ids.add(event.event_id)
            valid_events.append(event)
        except (ValueError, ValidationError):
            rejected += 1

    if valid_events:
        event_ids = [event.event_id for event in valid_events]
        existing_rows = session.exec(
            select(TelemetryEventRecord).where(
                TelemetryEventRecord.event_id.in_(event_ids)
            )
        ).all()
        existing_ids = {
            row.event_id if hasattr(row, "event_id") else row[0].event_id
            for row in existing_rows
        }

        rows = []
        for event in valid_events:
            if event.event_id in existing_ids or event.event_id in duplicate_in_batch:
                rejected += 1
                continue
            rows.append(_to_record_row(event))

        if rows:
            # Single bulk insert for the whole accepted batch.
            session.execute(sa_insert(TelemetryEventRecord), rows)
            session.commit()
            stored = len(rows)
        else:
            stored = 0
    else:
        stored = 0

    logger.info(
        "Telemetry batch processed: received=%d stored=%d rejected=%d",
        received,
        stored,
        rejected,
    )

    return {
        "received": received,
        "stored": stored,
        "rejected": rejected,
    }


def _parse_datetime(iso_str: str) -> datetime:
    """Convert ISO-8601 string to timezone-aware datetime."""
    return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))


def _validate_event(event: TelemetryEvent) -> None:
    """Validaciones adicionales más allá de Pydantic."""
    event_name = event.event_name

    # Validar warehouse según el evento
    if event_name in (
        "receiving_order_created",
        "dispatch_order_created",
        "stock_threshold_triggered",
        "direct_stock_edit_rejected",
        "dispatch_order_failed",
        "receiving_order_failed",
        "dispatch_form_abandoned",
    ):
        if event.warehouse is None:
            raise ValueError(f"warehouse is required for event '{event_name.value}'")
        if event.warehouse not in ("los_angeles", "zaragoza"):
            raise ValueError(f"Invalid warehouse '{event.warehouse}' for event '{event_name.value}'")

    # Validar source según el evento
    if event_name in ("dispatch_form_abandoned", "inbound_order_submitted", "outbound_order_submitted"):
        if event.source != "backoffice-web":
            raise ValueError(
                f"Event '{event_name.value}' must have source='backoffice-web', got '{event.source}'"
            )


def _to_record_row(event: TelemetryEvent) -> dict[str, Any]:
    """Map validated envelope event to telemetry_events table row."""
    return {
        "event_id": event.event_id,
        "event_type": event.event_name.value,
        "timestamp": _parse_datetime(event.occurred_at),
        "source": event.source.value,
        "tags": {
            "event_version": event.event_version,
            "warehouse": event.warehouse,
            "correlation_id": event.correlation_id,
        },
        "payload": event.payload,
        "processing_mode": event.processing_mode.value,
    }