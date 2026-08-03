"""Structured run trace for RFP workflow nodes (agent, input, output, timestamp)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def make_trace_entry(
    *,
    agent: str,
    input_payload: Any,
    output_payload: Any,
    part: int | None = None,
    department_id: str | None = None,
) -> dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": agent,
        "input": input_payload,
        "output": output_payload,
        "part": part,
        "department_id": department_id,
    }


def append_trace(existing: list[dict[str, Any]] | None, entry: dict[str, Any]) -> list[dict[str, Any]]:
    trace = list(existing or [])
    trace.append(entry)
    return trace
