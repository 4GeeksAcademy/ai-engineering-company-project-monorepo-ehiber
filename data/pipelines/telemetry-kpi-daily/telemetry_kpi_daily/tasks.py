"""Prefect tasks for telemetry KPI pipeline stages."""

from __future__ import annotations

from datetime import date
from typing import Any

from prefect import task

from telemetry_kpi_daily.caching import TRANSFORM_CACHE_EXPIRATION, transform_cache_key_fn
from telemetry_kpi_daily.config import PipelineConfig
from telemetry_kpi_daily.db import get_session
from telemetry_kpi_daily.stages.extract import events_to_records, extract_events
from telemetry_kpi_daily.stages.load import load_metrics
from telemetry_kpi_daily.stages.transform import transform_metrics
from telemetry_kpi_daily.stages.validate import validate_events


@task(name="extract_telemetry_events")
def extract_task(processing_date: date, config: PipelineConfig) -> dict[str, Any]:
    session = get_session()
    try:
        events = extract_events(session, processing_date)
        return {
            "processing_date": processing_date.isoformat(),
            "events": events_to_records(events),
            "events_extracted": len(events),
            "cursor": {
                "last_occurred_at": events[-1].timestamp.isoformat() if events else None,
                "last_event_id": events[-1].event_id if events else None,
            },
        }
    finally:
        session.close()


@task(name="validate_telemetry_events")
def validate_task(extracted: dict[str, Any]) -> dict[str, Any]:
    """Optional validation — schema drift must not block KPI delivery."""
    valid, rejected = validate_events(extracted["events"])
    return {
        **extracted,
        "valid_count": len(valid),
        "events_rejected": len(rejected),
        "rejected": rejected,
    }


@task(
    name="transform_kpi_metrics",
    cache_key_fn=transform_cache_key_fn,
    cache_expiration=TRANSFORM_CACHE_EXPIRATION,
)
def transform_task(processing_date: date) -> dict[str, Any]:
    session = get_session()
    try:
        metrics = transform_metrics(session, processing_date)
        return {"processing_date": processing_date.isoformat(), "metrics": metrics}
    finally:
        session.close()


@task(name="load_kpi_mart")
def load_task(
    transformed: dict[str, Any],
    *,
    run_id: str,
    config: PipelineConfig,
) -> dict[str, Any]:
    session = get_session()
    try:
        written = load_metrics(
            session,
            transformed["metrics"],
            run_id=run_id,
            schema_version=config.schema_version,
        )
        return {"metrics_written": written}
    finally:
        session.close()
