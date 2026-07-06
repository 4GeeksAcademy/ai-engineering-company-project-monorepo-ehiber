from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from trackflow_api.models import TelemetryKpiDaily
from trackflow_api.repositories.pipeline_repository import dimensions_key, upsert_kpi_rows


def metrics_to_rows(
    metrics: dict[str, list[dict[str, Any]]],
    *,
    run_id: str,
    schema_version: str,
) -> list[TelemetryKpiDaily]:
    computed_at = datetime.now(timezone.utc)
    rows: list[TelemetryKpiDaily] = []

    for record in metrics.get("order_fulfillment_rate", []):
        business_date = date.fromisoformat(str(record["date"]))
        dims = {
            "successful": record.get("successful"),
            "failed_insufficient": record.get("failed_insufficient"),
            "total": record.get("total"),
        }
        rows.append(
            TelemetryKpiDaily(
                metric_name="order_fulfillment_rate",
                business_date=business_date,
                warehouse=str(record["warehouse"]),
                dimensions_key=dimensions_key(dims),
                dimensions=dims,
                value=float(record["fulfillment_rate_pct"])
                if record.get("fulfillment_rate_pct") is not None
                else None,
                sample_size=int(record["total"]) if record.get("total") is not None else None,
                computed_at=computed_at,
                pipeline_run_id=run_id,
                schema_version=schema_version,
            )
        )

    for record in metrics.get("stock_discrepancy_frequency", []):
        business_date = date.fromisoformat(str(record["date"]))
        dims: dict[str, Any] = {}
        count = int(record.get("rejection_count") or 0)
        rows.append(
            TelemetryKpiDaily(
                metric_name="stock_discrepancy_frequency",
                business_date=business_date,
                warehouse=str(record["warehouse"]),
                dimensions_key=dimensions_key(dims),
                dimensions=dims,
                value=float(count),
                sample_size=count,
                computed_at=computed_at,
                pipeline_run_id=run_id,
                schema_version=schema_version,
            )
        )

    for record in metrics.get("receiving_dispatch_cycle_time", []):
        business_date = date.fromisoformat(str(record["date"]))
        dims = {}
        rows.append(
            TelemetryKpiDaily(
                metric_name="receiving_dispatch_cycle_time",
                business_date=business_date,
                warehouse=str(record["warehouse"]),
                dimensions_key=dimensions_key(dims),
                dimensions=dims,
                value=float(record["avg_cycle_hours"])
                if record.get("avg_cycle_hours") is not None
                else None,
                sample_size=int(record["sample_size"])
                if record.get("sample_size") is not None
                else None,
                computed_at=computed_at,
                pipeline_run_id=run_id,
                schema_version=schema_version,
            )
        )

    return rows


def load_metrics(
    session,
    metrics: dict[str, list[dict[str, Any]]],
    *,
    run_id: str,
    schema_version: str,
) -> int:
    rows = metrics_to_rows(metrics, run_id=run_id, schema_version=schema_version)
    return upsert_kpi_rows(session, rows)
