from __future__ import annotations

import threading
from typing import Any

from .types import FailureType

_LOCK = threading.Lock()
_COUNTERS: dict[str, int] = {
    "structural": 0,
    "content": 0,
    "security": 0,
}
_BY_GUARDRAIL: dict[str, int] = {}


def record_guardrail_event(
    *,
    failure_type: FailureType,
    guardrail: str,
    reason: str | None = None,
) -> dict[str, Any]:
    with _LOCK:
        _COUNTERS[failure_type] = _COUNTERS.get(failure_type, 0) + 1
        _BY_GUARDRAIL[guardrail] = _BY_GUARDRAIL.get(guardrail, 0) + 1
        snapshot = {
            "failure_type": failure_type,
            "guardrail": guardrail,
            "reason": reason,
            "totals": dict(_COUNTERS),
            "by_guardrail": dict(_BY_GUARDRAIL),
        }
    return snapshot


def get_guardrail_stats() -> dict[str, Any]:
    with _LOCK:
        return {
            "by_failure_type": dict(_COUNTERS),
            "by_guardrail": dict(_BY_GUARDRAIL),
            "total": sum(_COUNTERS.values()),
        }


def reset_guardrail_stats() -> None:
    with _LOCK:
        for key in list(_COUNTERS):
            _COUNTERS[key] = 0
        _BY_GUARDRAIL.clear()
