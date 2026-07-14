"""Trigger telemetry KPI pipeline without duplicating orchestration logic."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Any

from ..core.config import find_repo_root

_REPO_ROOT = find_repo_root()
_PIPELINES_DIR = _REPO_ROOT / "data" / "pipelines"
_PIPELINE_PKG = _PIPELINES_DIR / "telemetry-kpi-daily"
_SERVICES_API = _REPO_ROOT / "services" / "trackflow-api"
_SERVICES = _REPO_ROOT / "services"


def _ensure_pipeline_import_path() -> None:
    for path in (_PIPELINE_PKG, _PIPELINES_DIR, _SERVICES_API, _SERVICES):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


def trigger_telemetry_kpi_daily_flow(
    *,
    processing_date: date | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    force: bool = False,
    triggered_by: str = "manual",
) -> dict[str, Any]:
    _ensure_pipeline_import_path()
    from pipeline import telemetry_kpi_daily_flow  # noqa: WPS433 — rubric: import from data/pipelines

    return telemetry_kpi_daily_flow(
        processing_date=processing_date,
        start_date=start_date,
        end_date=end_date,
        triggered_by=triggered_by,
        force=force,
    )


def trigger_telemetry_kpi_daily_direct(
    processing_date: date,
    *,
    force: bool = False,
    triggered_by: str = "nightly-script",
) -> dict[str, Any]:
    """Run the KPI pipeline without Prefect (standalone script path)."""
    _ensure_pipeline_import_path()
    from telemetry_kpi_daily.pipeline_core import process_processing_date  # noqa: WPS433

    result = process_processing_date(
        processing_date,
        triggered_by=triggered_by,
        force=force,
    )
    return {
        "processing_date": result.processing_date.isoformat(),
        "run_id": result.run_id,
        "status": result.status,
        "events_extracted": result.events_extracted,
        "events_rejected": result.events_rejected,
        "metrics_written": result.metrics_written,
        "error": result.error,
    }


def run_telemetry_pipeline_direct_job(
    *,
    processing_date: date | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    force: bool = False,
    triggered_by: str = "celery-worker",
) -> dict[str, Any]:
    """Run the KPI pipeline for one or more dates without Prefect Cloud."""
    _ensure_pipeline_import_path()
    from telemetry_kpi_daily.config import load_config, resolve_processing_dates  # noqa: WPS433

    config = load_config()
    dates = resolve_processing_dates(
        processing_date=processing_date,
        start_date=start_date,
        end_date=end_date,
        late_data_days=config.late_data_days,
    )

    results: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    for day in dates:
        try:
            summary = trigger_telemetry_kpi_daily_direct(
                day,
                force=force,
                triggered_by=triggered_by,
            )
            if summary["status"] == "failed":
                failures.append(
                    {
                        "processing_date": day.isoformat(),
                        "run_id": summary.get("run_id", ""),
                        "error": summary.get("error") or "pipeline failed",
                    }
                )
            results.append(summary)
        except Exception as exc:
            failures.append(
                {
                    "processing_date": day.isoformat(),
                    "run_id": "",
                    "error": str(exc),
                }
            )

    if failures and not any(item["status"] in {"succeeded", "skipped"} for item in results):
        raise RuntimeError(failures[0]["error"])

    return {
        "pipeline_name": config.pipeline_name,
        "processed_dates": [item["processing_date"] for item in results],
        "succeeded": sum(1 for item in results if item["status"] == "succeeded"),
        "skipped": sum(1 for item in results if item["status"] == "skipped"),
        "failed": len(failures),
        "failures": failures,
        "results": results,
    }
