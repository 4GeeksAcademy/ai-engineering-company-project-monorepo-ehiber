"""Task cache helpers (no Prefect import — testable in isolation)."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

TRANSFORM_CACHE_EXPIRATION = timedelta(hours=1)


def transform_cache_key_fn(_task_run_context: dict[str, Any], task_parameters: dict[str, Any]) -> str:
    processing_date = task_parameters["processing_date"]
    iso = processing_date.isoformat() if isinstance(processing_date, date) else str(processing_date)
    return f"transform-kpi-metrics:{iso}"
