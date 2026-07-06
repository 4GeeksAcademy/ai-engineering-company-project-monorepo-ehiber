"""Validate extracted telemetry events against event-schemas.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from telemetry_kpi_daily.config import SCHEMA_PATH


def _load_schema(path: Path | None = None) -> dict[str, Any]:
    schema_path = path or SCHEMA_PATH
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_events(
    events: list[dict[str, Any]],
    *,
    schema_path: Path | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    schema = _load_schema(schema_path)
    event_defs = schema.get("events", {})
    valid: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for event in events:
        event_type = event.get("event_type")
        definition = event_defs.get(event_type)
        if definition is None:
            rejected.append({"event_id": event.get("event_id"), "reason": "unknown_event_type"})
            continue

        allowed = set(definition.get("allowed_payload_properties", []))
        payload = event.get("payload") or {}
        extra_keys = set(payload.keys()) - allowed
        if extra_keys:
            rejected.append(
                {
                    "event_id": event.get("event_id"),
                    "reason": f"extra_payload_keys:{sorted(extra_keys)}",
                }
            )
            continue

        warehouse_required = event_type not in ("user_login_failed",)
        warehouse = event.get("warehouse")
        if warehouse_required and not warehouse:
            rejected.append({"event_id": event.get("event_id"), "reason": "missing_warehouse"})
            continue

        valid.append(event)

    return valid, rejected
