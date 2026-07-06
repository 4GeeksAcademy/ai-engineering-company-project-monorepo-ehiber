"""Read KPI aggregates from telemetry_kpi_daily mart."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlmodel import Session

from ..repositories.pipeline_repository import list_kpi_rows


def _rows_to_metrics(rows: list) -> dict[str, list[dict[str, Any]]]:
    metrics: dict[str, list[dict[str, Any]]] = {
        "order_fulfillment_rate": [],
        "stock_discrepancy_frequency": [],
        "receiving_dispatch_cycle_time": [],
    }
    for row in rows:
        record: dict[str, Any] = {
            "date": row.business_date.isoformat(),
            "warehouse": row.warehouse,
        }
        record.update(row.dimensions or {})
        if row.metric_name == "order_fulfillment_rate":
            record["fulfillment_rate_pct"] = row.value
            metrics["order_fulfillment_rate"].append(record)
        elif row.metric_name == "stock_discrepancy_frequency":
            record["rejection_count"] = int(row.value) if row.value is not None else 0
            metrics["stock_discrepancy_frequency"].append(record)
        elif row.metric_name == "receiving_dispatch_cycle_time":
            record["avg_cycle_hours"] = row.value
            if row.sample_size is not None:
                record["sample_size"] = row.sample_size
            metrics["receiving_dispatch_cycle_time"].append(record)
    return metrics


def get_metrics_from_mart(
    session: Session,
    start_date: date,
    end_date: date,
) -> dict[str, list[dict[str, Any]]] | None:
    rows = list_kpi_rows(session, start_date=start_date, end_date=end_date)
    if not rows:
        return None
    return _rows_to_metrics(rows)
