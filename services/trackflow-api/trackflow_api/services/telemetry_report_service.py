from __future__ import annotations

from datetime import datetime

from sqlmodel import Session

from ..core.cache import TELEMETRY_REPORT_KEY, cache_get, cache_invalidate_prefix, cache_set
from ..domain.telemetry.report import build_telemetry_report

TELEMETRY_REPORT_CACHE_TTL_SECONDS = 300


def invalidate_telemetry_report_cache() -> None:
    cache_invalidate_prefix("telemetry:")


def get_telemetry_report(
    session: Session,
    *,
    since: datetime | None = None,
    force_refresh: bool = False,
) -> dict:
    cache_key = TELEMETRY_REPORT_KEY if since is None else f"{TELEMETRY_REPORT_KEY}:since={since.isoformat()}"

    if not force_refresh:
        cached = cache_get(cache_key)
        if cached is not None:
            return cached

    report = build_telemetry_report(session, since=since)
    cache_set(cache_key, report, TELEMETRY_REPORT_CACHE_TTL_SECONDS)
    return report
