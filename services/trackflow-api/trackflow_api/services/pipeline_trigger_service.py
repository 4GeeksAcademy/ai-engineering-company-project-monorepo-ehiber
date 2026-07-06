"""Trigger telemetry KPI pipeline without duplicating orchestration logic."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[4]
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
