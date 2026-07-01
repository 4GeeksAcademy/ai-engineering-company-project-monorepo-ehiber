"""Read access for persisted telemetry events."""

from __future__ import annotations

from datetime import datetime

from sqlmodel import Session, select

from ..models import TelemetryEvent

KPI_EVENT_TYPES = (
    "dispatch_order_created",
    "dispatch_order_failed",
    "direct_stock_edit_rejected",
    "receiving_order_created",
)


def list_kpi_events(
    session: Session,
    *,
    since: datetime | None = None,
) -> list[TelemetryEvent]:
    statement = select(TelemetryEvent).where(
        TelemetryEvent.event_type.in_(KPI_EVENT_TYPES)
    )
    if since is not None:
        statement = statement.where(TelemetryEvent.timestamp >= since)
    statement = statement.order_by(TelemetryEvent.timestamp)
    return list(session.exec(statement).all())
