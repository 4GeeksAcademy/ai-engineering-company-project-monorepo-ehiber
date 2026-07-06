from __future__ import annotations

from datetime import date
from typing import Any

from prefect import flow

from telemetry_kpi_daily.config import load_config, resolve_processing_dates
from telemetry_kpi_daily.db import get_session
from telemetry_kpi_daily.orchestration import run_processing_date_with_subflows
from telemetry_kpi_daily.pipeline_core import DateRunResult
from telemetry_kpi_daily.subflows import (
    extract_subflow,
    load_subflow,
    transform_subflow,
    validate_subflow,
)

from trackflow_api.repositories.pipeline_repository import (
    create_run,
    finalize_run,
    get_watermark,
    has_recent_success,
    mark_run_skipped,
    update_watermark,
)


def _run_date_etl_subflows(
    processing_date: date,
    *,
    config,
    triggered_by: str,
    force: bool,
) -> DateRunResult:
    """Run ledger + extract → validate → transform → load subflows for one date."""
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
        extracted = extract_subflow(processing_date, config)
        validated = validate_subflow(extracted)
        transformed = transform_subflow(processing_date)
        loaded = load_subflow(transformed, run_id=run.run_id, config=config)

        session = get_session()
        try:
            cursor = extracted["cursor"]
            watermark_after = cursor
            if cursor.get("last_occurred_at"):
                from datetime import datetime

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


@flow(name="telemetry-kpi-daily-date-flow", log_prints=True)
def process_date_flow(
    processing_date: date,
    *,
    triggered_by: str = "scheduler",
    force: bool = False,
) -> DateRunResult:
    config = load_config()
    return _run_date_etl_subflows(
        processing_date,
        config=config,
        triggered_by=triggered_by,
        force=force,
    )


@flow(name="telemetry-kpi-daily-flow", log_prints=True)
def telemetry_kpi_daily_flow(
    processing_date: date | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    triggered_by: str = "scheduler",
    force: bool = False,
) -> dict[str, Any]:
    """Main deployment flow — invokes ETL subflows per processing_date."""
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
            session = get_session()
            try:
                watermark_before = get_watermark(session, config.pipeline_name)
                if not force and has_recent_success(session, processing_date=day):
                    run = create_run(
                        session,
                        processing_date=day,
                        triggered_by=triggered_by,
                        watermark_before=watermark_before,
                    )
                    mark_run_skipped(
                        session,
                        run,
                        reason=(
                            f"successful run within last "
                            f"{config.skip_if_success_within_hours}h"
                        ),
                    )
                    results.append(
                        DateRunResult(
                            processing_date=day,
                            run_id=run.run_id,
                            status="skipped",
                        )
                    )
                    continue

                run = create_run(
                    session,
                    processing_date=day,
                    triggered_by=triggered_by,
                    watermark_before=watermark_before,
                )
            finally:
                session.close()

            extracted = extract_subflow(day, config)
            validated = validate_subflow(extracted)
            transformed = transform_subflow(day)
            loaded = load_subflow(transformed, run_id=run.run_id, config=config)

            session = get_session()
            try:
                from datetime import datetime

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

            results.append(
                DateRunResult(
                    processing_date=day,
                    run_id=run.run_id,
                    status="succeeded",
                    events_extracted=validated["events_extracted"],
                    events_rejected=validated["events_rejected"],
                    metrics_written=loaded["metrics_written"],
                )
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
    return {"status": "not_implemented", "pipeline_name": "telemetry-stream-alerts"}
