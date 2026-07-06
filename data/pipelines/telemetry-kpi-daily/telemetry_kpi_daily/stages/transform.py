from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from sqlmodel import Session

_SERVICES = Path(__file__).resolve().parents[5] / "services"
if str(_SERVICES) not in sys.path:
    sys.path.insert(0, str(_SERVICES))

from telemetry.analysis import build_metrics  # noqa: E402


def transform_metrics(
    session: Session,
    processing_date: date,
) -> dict[str, list[dict[str, Any]]]:
    return build_metrics(session, processing_date, processing_date)
