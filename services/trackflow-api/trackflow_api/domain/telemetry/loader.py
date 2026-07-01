"""Load telemetry events from the database into a normalized Pandas DataFrame."""

from __future__ import annotations

from typing import Any

import pandas as pd

from ...models import TelemetryEvent

_PAYLOAD_FIELDS = (
    "sku_id",
    "sku_code",
    "client_id",
    "warehouse",
    "quantity",
    "failure_reason",
    "receiving_order_id",
    "dispatch_order_id",
    "rejection_reason",
)


def _resolve_warehouse(tags: dict[str, Any], payload: dict[str, Any]) -> str | None:
    warehouse = tags.get("warehouse")
    if warehouse:
        return warehouse
    payload_warehouse = payload.get("warehouse")
    if payload_warehouse:
        return payload_warehouse
    return None


def events_to_dataframe(events: list[TelemetryEvent]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for event in events:
        payload = event.payload or {}
        tags = event.tags or {}
        row: dict[str, Any] = {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "timestamp": event.timestamp,
            "source": event.source,
            "warehouse": _resolve_warehouse(tags, payload),
        }
        for field in _PAYLOAD_FIELDS:
            row[field] = payload.get(field)
        rows.append(row)

    if not rows:
        return pd.DataFrame(
            columns=[
                "event_id",
                "event_type",
                "timestamp",
                "source",
                "warehouse",
                *_PAYLOAD_FIELDS,
                "date",
            ]
        )

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["date"] = df["timestamp"].dt.date
    return df
