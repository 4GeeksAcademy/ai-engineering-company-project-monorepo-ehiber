from __future__ import annotations

import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from sqlmodel import Session

from ..core.cache import TELEMETRY_REPORT_KEY, cache_get, cache_invalidate_prefix, cache_set

_SERVICES_DIR = Path(__file__).resolve().parents[3]
if str(_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVICES_DIR))

from telemetry.analysis import build_metrics  # noqa: E402

TELEMETRY_REPORT_CACHE_TTL_SECONDS = 60
DEFAULT_REPORT_WINDOW_DAYS = 7


def invalidate_telemetry_report_cache() -> None:
    cache_invalidate_prefix("telemetry:")


def _report_cache_key(start_date: date, end_date: date) -> str:
    return (
        f"{TELEMETRY_REPORT_KEY}:start={start_date.isoformat()}:end={end_date.isoformat()}"
    )


def resolve_report_window(
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> tuple[date, date]:
    resolved_end = end_date or datetime.now(timezone.utc).date()
    resolved_start = start_date or (resolved_end - timedelta(days=DEFAULT_REPORT_WINDOW_DAYS))
    return resolved_start, resolved_end


def get_telemetry_report(
    session: Session,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    force_refresh: bool = False,
) -> dict:
    resolved_start, resolved_end = resolve_report_window(
        start_date=start_date,
        end_date=end_date,
    )
    cache_key = _report_cache_key(resolved_start, resolved_end)

    if not force_refresh:
        cached = cache_get(cache_key)
        if cached is not None:
            return cached

    report = {
        "period": {
            "start_date": resolved_start.isoformat(),
            "end_date": resolved_end.isoformat(),
        },
        "metrics": build_metrics(session, resolved_start, resolved_end),
    }
    cache_set(cache_key, report, TELEMETRY_REPORT_CACHE_TTL_SECONDS)
    return report
