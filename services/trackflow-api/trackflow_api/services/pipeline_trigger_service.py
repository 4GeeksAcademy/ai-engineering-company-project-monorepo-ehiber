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
) -> dict[str, Any]:
    _ensure_pipeline_import_path()
    from pipeline import telemetry_kpi_daily_flow  # noqa: WPS433 — rubric: import from data/pipelines

    return telemetry_kpi_daily_flow(
        processing_date=processing_date,
        start_date=start_date,
        end_date=end_date,
        triggered_by="manual",
        force=force,
    )
