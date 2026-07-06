from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from prefect import flow, task

from telemetry_kpi_daily.caching import TRANSFORM_CACHE_EXPIRATION, transform_cache_key_fn

from telemetry_kpi_daily.config import PipelineConfig, load_config, resolve_processing_dates
from telemetry_kpi_daily.db import get_session
from telemetry_kpi_daily.pipeline_core import DateRunResult
from telemetry_kpi_daily.stages.extract import events_to_records, extract_events
from telemetry_kpi_daily.stages.load import load_metrics
from telemetry_kpi_daily.stages.transform import transform_metrics
from telemetry_kpi_daily.stages.validate import validate_events

from trackflow_api.repositories.pipeline_repository import (
    create_run,
    finalize_run,
    get_watermark,
    has_recent_success,
    mark_run_skipped,
    update_watermark,
)

# 3 retries × 30s delay: Supabase/Postgres transient blips (cold start, pool timeout)
# usually clear within ~90s; beyond that errors tend to be config/network issues
# that immediate retries won't fix — fail fast after the third attempt.
EXTRACT_LOAD_RETRIES = 3
EXTRACT_LOAD_RETRY_DELAY_SECONDS = 30


def _retry_kwargs(config: PipelineConfig, stage: str) -> dict[str, int]:
    if stage == "extract":
        return {
            "retries": config.extract_retries,
            "retry_delay_seconds": config.extract_retry_delay_seconds,
        }
    if stage == "load":
        return {
            "retries": config.load_retries,
            "retry_delay_seconds": config.load_retry_delay_seconds,
        }
    return {"retries": 0, "retry_delay_seconds": 0}


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


@task(name="validate_telemetry_events", allow_failure=True)
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


def _coalesce_validation(extracted: dict[str, Any], validation_state) -> dict[str, Any]:
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


@flow(name="telemetry-kpi-daily-date-flow", log_prints=True)
def process_date_flow(
    processing_date: date,
    *,
    triggered_by: str = "scheduler",
    force: bool = False,
) -> DateRunResult:
    config = load_config()
    session = get_session()
    try:
        watermark_before = get_watermark(session, config.pipeline_name)
        if not force and has_recent_success(session, processing_date=processing_date):
            run = create_run(
                session,
                processing_date=processing_date,
                triggered_by=triggered_by,
                watermark_before=watermark_before,
            )
            mark_run_skipped(
                session,
                run,
                reason=f"successful run within last {config.skip_if_success_within_hours}h",
            )
            return DateRunResult(
                processing_date=processing_date,
                run_id=run.run_id,
                status="skipped",
            )

        run = create_run(
            session,
            processing_date=processing_date,
            triggered_by=triggered_by,
            watermark_before=watermark_before,
        )
    finally:
        session.close()

    try:
        extracted = extract_task.with_options(**_retry_kwargs(config, "extract"))(processing_date, config)
        validation_state = validate_task.with_options(allow_failure=True)(extracted, return_state=True)
        validated = _coalesce_validation(extracted, validation_state)
        transformed = transform_task(processing_date)
        loaded = load_task.with_options(**_retry_kwargs(config, "load"))(
            transformed,
            run_id=run.run_id,
            config=config,
        )

        session = get_session()
        try:
            cursor = extracted["cursor"]
            watermark_after = cursor
            if cursor.get("last_occurred_at"):
                update_watermark(
                    session,
                    pipeline_name=config.pipeline_name,
                    run_id=run.run_id,
                    last_occurred_at=datetime.fromisoformat(cursor["last_occurred_at"]),
                    last_event_id=cursor.get("last_event_id"),
                )
            finalize_run(
                session,
                run,
                status="succeeded",
                events_extracted=validated["events_extracted"],
                events_rejected=validated["events_rejected"],
                metrics_written=loaded["metrics_written"],
                watermark_after=watermark_after,
            )
        finally:
            session.close()

        return DateRunResult(
            processing_date=processing_date,
            run_id=run.run_id,
            status="succeeded",
            events_extracted=validated["events_extracted"],
            events_rejected=validated["events_rejected"],
            metrics_written=loaded["metrics_written"],
        )
    except Exception as exc:
        session = get_session()
        try:
            finalize_run(
                session,
                run,
                status="failed",
                events_extracted=0,
                events_rejected=0,
                metrics_written=0,
                watermark_after=watermark_before,
                error_summary=str(exc),
            )
        finally:
            session.close()
        return DateRunResult(
            processing_date=processing_date,
            run_id=run.run_id,
            status="failed",
            error=str(exc),
        )


@flow(name="telemetry-kpi-daily-flow", log_prints=True)
def telemetry_kpi_daily_flow(
    processing_date: date | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    triggered_by: str = "scheduler",
    force: bool = False,
) -> dict[str, Any]:
    config = load_config()
    dates = resolve_processing_dates(
        processing_date=processing_date,
        start_date=start_date,
        end_date=end_date,
        late_data_days=config.late_data_days,
    )

    results: list[DateRunResult] = []
    failures: list[dict[str, str]] = []

    for day in dates:
        try:
            result = process_date_flow(
                day,
                triggered_by=triggered_by,
                force=force,
            )
            results.append(result)
            if result.status == "failed":
                failures.append(
                    {
                        "processing_date": day.isoformat(),
                        "run_id": result.run_id,
                        "error": result.error or "unknown",
                    }
                )
        except Exception as exc:
            failures.append(
                {
                    "processing_date": day.isoformat(),
                    "run_id": "",
                    "error": str(exc),
                }
            )

    return {
        "pipeline_name": config.pipeline_name,
        "processed_dates": [item.processing_date.isoformat() for item in results],
        "succeeded": sum(1 for item in results if item.status == "succeeded"),
        "skipped": sum(1 for item in results if item.status == "skipped"),
        "failed": len(failures),
        "failures": failures,
        "results": [
            {
                "processing_date": item.processing_date.isoformat(),
                "run_id": item.run_id,
                "status": item.status,
                "events_extracted": item.events_extracted,
                "events_rejected": item.events_rejected,
                "metrics_written": item.metrics_written,
                "error": item.error,
            }
            for item in results
        ],
    }


@flow(name="telemetry-stream-alerts-flow", log_prints=True)
def telemetry_stream_alerts_flow() -> dict[str, str]:
    """Placeholder flow for stream events — implementation deferred to phase 2."""
    return {"status": "not_implemented", "pipeline_name": "telemetry-stream-alerts"}
