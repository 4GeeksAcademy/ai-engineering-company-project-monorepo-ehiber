from __future__ import annotations

import threading
import time
from typing import Any

_LOCK = threading.Lock()
_TRACES: dict[str, dict[str, Any]] = {}


def store_trace(run_id: str, payload: dict[str, Any]) -> None:
    with _LOCK:
        _TRACES[run_id] = payload


def get_trace(run_id: str) -> dict[str, Any] | None:
    with _LOCK:
        payload = _TRACES.get(run_id)
        return dict(payload) if payload is not None else None


def clear_traces() -> None:
    with _LOCK:
        _TRACES.clear()


def timed_step(node: str, detail: dict[str, Any] | None = None, *, status: str = "ok") -> dict[str, Any]:
    return {
        "node": node,
        "status": status,
        "ms": 0,
        "detail": detail or {},
        "ts": time.time(),
    }
