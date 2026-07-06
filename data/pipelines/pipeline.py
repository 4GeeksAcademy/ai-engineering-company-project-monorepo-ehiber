"""
Canonical Prefect entrypoint for TrackFlow data pipelines.

Rubric / deployment entrypoint: ``data/pipelines/pipeline.py:telemetry_kpi_daily_flow``
Implementation lives in ``telemetry-kpi-daily/telemetry_kpi_daily/``.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PIPELINE_PKG = Path(__file__).resolve().parent / "telemetry-kpi-daily"
if str(_PIPELINE_PKG) not in sys.path:
    sys.path.insert(0, str(_PIPELINE_PKG))

from telemetry_kpi_daily.flows import (  # noqa: E402
    extract_task,
    load_task,
    process_date_flow,
    telemetry_kpi_daily_flow,
    telemetry_stream_alerts_flow,
    transform_task,
    validate_task,
)

__all__ = [
    "extract_task",
    "validate_task",
    "transform_task",
    "load_task",
    "process_date_flow",
    "telemetry_kpi_daily_flow",
    "telemetry_stream_alerts_flow",
]
