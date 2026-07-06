from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from sqlmodel import Session, select

from trackflow_api.models import TelemetryEvent

KPI_EVENT_TYPES = (
    "dispatch_order_created",
    "dispatch_order_failed",
    "direct_stock_edit_rejected",
    "receiving_order_created",
)


def _day_bounds(processing_date: date) -> tuple[datetime, datetime]:
    start_dt = datetime.combine(processing_date, time.min, tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(days=1)
    return start_dt, end_dt


def extract_events(session: Session, processing_date: date) -> list[TelemetryEvent]:
    start_dt, end_dt = _day_bounds(processing_date)
    statement = (
        select(TelemetryEvent)
        .where(TelemetryEvent.event_type.in_(KPI_EVENT_TYPES))
        .where(TelemetryEvent.timestamp >= start_dt)
        .where(TelemetryEvent.timestamp < end_dt)
        .order_by(TelemetryEvent.timestamp, TelemetryEvent.event_id)
    )
    return list(session.exec(statement).all())


def latest_event_cursor(events: list[TelemetryEvent]) -> tuple[datetime | None, str | None]:
    if not events:
        return None, None
    last = events[-1]
    return last.timestamp, last.event_id


def events_to_records(events: list[TelemetryEvent]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in events:
        payload = event.payload or {}
        tags = event.tags or {}
        rows.append(
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "timestamp": event.timestamp,
                "source": event.source,
                "warehouse": tags.get("warehouse") or payload.get("warehouse"),
                "payload": payload,
            }
        )
    return rows
