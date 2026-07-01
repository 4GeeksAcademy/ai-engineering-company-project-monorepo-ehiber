"""Orchestrate telemetry KPI calculations into a serializable report."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session

from ...repositories import telemetry_repository
from .kpi_cycle_time import compute_receiving_dispatch_cycle_time
from .kpi_fulfillment import compute_fulfillment_rate
from .kpi_stock_discrepancies import compute_stock_discrepancy_frequency
from .loader import events_to_dataframe


def build_telemetry_report(
    session: Session,
    *,
    since: datetime | None = None,
) -> dict[str, Any]:
    events = telemetry_repository.list_kpi_events(session, since=since)
    df = events_to_dataframe(events)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period": {
            "since": since.isoformat() if since is not None else None,
        },
        "event_count": len(events),
        "kpis": [
            compute_fulfillment_rate(df),
            compute_stock_discrepancy_frequency(df),
            compute_receiving_dispatch_cycle_time(df),
        ],
    }
