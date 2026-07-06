from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from trackflow_api.repositories.pipeline_repository import (
    create_run,
    finalize_run,
    get_watermark,
    has_recent_success,
    mark_run_skipped,
    update_watermark,
)

from telemetry_kpi_daily.config import PipelineConfig, load_config
from telemetry_kpi_daily.db import get_session
from telemetry_kpi_daily.phases import (
    run_extract_phase,
    run_load_phase,
    run_transform_phase,
    run_validate_phase,
)


@dataclass
class DateRunResult:
    processing_date: date
    run_id: str
    status: str
    events_extracted: int = 0
    events_rejected: int = 0
    metrics_written: int = 0
    error: str | None = None


def process_processing_date(
    processing_date: date,
    *,
    config: PipelineConfig | None = None,
    triggered_by: str = "manual",
    force: bool = False,
) -> DateRunResult:
    """Direct Python path (--no-prefect) — same stage functions as subflows."""
    cfg = config or load_config()
    session = get_session()
    try:
        watermark_before = get_watermark(session, cfg.pipeline_name)
        if not force and has_recent_success(
            session,
            processing_date=processing_date,
            pipeline_name=cfg.pipeline_name,
            within=timedelta(hours=cfg.skip_if_success_within_hours),
        ):
            run = create_run(
                session,
                processing_date=processing_date,
                triggered_by=triggered_by,
                watermark_before=watermark_before,
            )
            mark_run_skipped(
                session,
                run,
                reason=f"successful run within last {cfg.skip_if_success_within_hours}h",
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

        try:
            extracted = run_extract_phase(processing_date, cfg)
            validated = run_validate_phase(extracted)
            transformed = run_transform_phase(processing_date)
            loaded = run_load_phase(transformed, run_id=run.run_id, config=cfg)

            cursor = extracted["cursor"]
            watermark_after = cursor
            if cursor.get("last_occurred_at"):
                update_watermark(
                    session,
                    pipeline_name=cfg.pipeline_name,
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
            return DateRunResult(
                processing_date=processing_date,
                run_id=run.run_id,
                status="succeeded",
                events_extracted=validated["events_extracted"],
                events_rejected=validated["events_rejected"],
                metrics_written=loaded["metrics_written"],
            )
        except Exception as exc:
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
            return DateRunResult(
                processing_date=processing_date,
                run_id=run.run_id,
                status="failed",
                error=str(exc),
            )
    finally:
        session.close()


def run_pipeline(
    processing_dates: list[date],
    *,
    config: PipelineConfig | None = None,
    triggered_by: str = "manual",
    force: bool = False,
) -> dict[str, Any]:
    cfg = config or load_config()
    results: list[DateRunResult] = []
    failures: list[dict[str, str]] = []

    for processing_date in processing_dates:
        try:
            result = process_processing_date(
                processing_date,
                config=cfg,
                triggered_by=triggered_by,
                force=force,
            )
            results.append(result)
            if result.status == "failed":
                failures.append(
                    {
                        "processing_date": processing_date.isoformat(),
                        "run_id": result.run_id,
                        "error": result.error or "unknown",
                    }
                )
        except Exception as exc:
            failures.append(
                {
                    "processing_date": processing_date.isoformat(),
                    "run_id": "",
                    "error": str(exc),
                }
            )

    return {
        "pipeline_name": cfg.pipeline_name,
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
