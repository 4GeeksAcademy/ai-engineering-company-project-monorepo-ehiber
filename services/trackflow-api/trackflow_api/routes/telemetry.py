"""
Endpoint stub de telemetría (Fase 2).

Valida el formato de los eventos entrantes y responde 200 sin persistir.
La implementación real con base de datos se añadirá en la Fase 3.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter
from pydantic import ValidationError

from ..schemas.telemetry import (
    ALLOWED_PAYLOAD_PROPERTIES,
    TelemetryBatchRequest,
    TelemetryEvent,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.post("/events")
async def ingest_telemetry_events(
    batch: TelemetryBatchRequest,
) -> dict[str, int]:
    """
    Recibe un lote de eventos de telemetría, valida el formato y responde 200.

    Es un stub temporal: no persiste nada. La persistencia real se implementa
    en la Fase 3 del plan de telemetría.
    """
    received = 0

    for event in batch.events:
        try:
            _validate_event(event)
            received += 1
        except (ValueError, ValidationError) as exc:
            logger.warning("Telemetry event rejected: event_id=%s error=%s", event.event_id, exc)

    logger.info(
        "Telemetry batch processed: received=%d",
        received,
    )

    return {"received": received}


def _validate_event(event: TelemetryEvent) -> None:
    """Validaciones adicionales más allá de Pydantic."""
    event_name = event.event_name
    allowed = ALLOWED_PAYLOAD_PROPERTIES.get(event_name, set())

    extra_keys = set(event.payload.keys()) - allowed
    if extra_keys:
        raise ValueError(
            f"Payload keys not allowed for '{event_name.value}': {sorted(extra_keys)}"
        )

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