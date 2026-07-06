"""Pure ETL phase runners — no Prefect import (testable without Cloud)."""

from __future__ import annotations

from datetime import date
from typing import Any

from telemetry_kpi_daily.config import PipelineConfig
from telemetry_kpi_daily.db import get_session
from telemetry_kpi_daily.stages.extract import events_to_records, extract_events
from telemetry_kpi_daily.stages.load import load_metrics
from telemetry_kpi_daily.stages.transform import transform_metrics
from telemetry_kpi_daily.stages.validate import validate_events


def coalesce_validation(extracted: dict[str, Any], validation_state) -> dict[str, Any]:
    if validation_state.is_completed():
        return validation_state.result()
    return {
        **extracted,
        "valid_count": len(extracted.get("events", [])),
        "events_rejected": 0,
        "rejected": [],
        "validation_skipped": True,
        "validation_error": str(getattr(validation_state, "message", "validation failed")),
    }


def run_extract_phase(processing_date: date, config: PipelineConfig) -> dict[str, Any]:
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


def run_validate_phase(extracted: dict[str, Any]) -> dict[str, Any]:
    valid, rejected = validate_events(extracted["events"])
    return {
        **extracted,
        "valid_count": len(valid),
        "events_rejected": len(rejected),
        "rejected": rejected,
    }


def run_transform_phase(processing_date: date) -> dict[str, Any]:
    session = get_session()
    try:
        metrics = transform_metrics(session, processing_date)
        return {"processing_date": processing_date.isoformat(), "metrics": metrics}
    finally:
        session.close()


def run_load_phase(
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
