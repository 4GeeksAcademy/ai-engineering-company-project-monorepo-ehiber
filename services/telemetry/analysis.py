"""
Telemetry KPI analysis pipeline.

Each public metric function follows:
load → filter → convert types → group → aggregate
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Any

import pandas as pd
from sqlmodel import Session, select

from trackflow_api.models import TelemetryEvent

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
    warehouse = tags.get("warehouse") or payload.get("warehouse")
    return warehouse or None


def _load_events(
    session: Session,
    event_types: tuple[str, ...],
    start_date: date,
    end_date: date,
) -> pd.DataFrame:
    start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=timezone.utc)

    statement = (
        select(TelemetryEvent)
        .where(TelemetryEvent.event_type.in_(event_types))
        .where(TelemetryEvent.timestamp >= start_dt)
        .where(TelemetryEvent.timestamp < end_dt)
        .order_by(TelemetryEvent.timestamp)
    )
    events = list(session.exec(statement).all())

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

    columns = [
        "event_id",
        "event_type",
        "timestamp",
        "source",
        "warehouse",
        *_PAYLOAD_FIELDS,
        "date",
    ]
    if not rows:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["date"] = df["timestamp"].dt.date
    return df


def _serialize_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    output = df.copy()
    if "date" in output.columns:
        output["date"] = output["date"].astype(str)
    output = output.where(pd.notna(output), None)
    return output.to_dict(orient="records")


def compute_fulfillment_rate(
    session: Session,
    start_date: date,
    end_date: date,
) -> list[dict[str, Any]]:
    df = _load_events(
        session,
        ("dispatch_order_created", "dispatch_order_failed"),
        start_date,
        end_date,
    )
    if df.empty:
        return []

    created = df[df["event_type"] == "dispatch_order_created"].copy()
    failed_stock = df[
        (df["event_type"] == "dispatch_order_failed")
        & (df["failure_reason"] == "insufficient_stock")
    ].copy()
    if created.empty and failed_stock.empty:
        return []

    created["outcome"] = "successful"
    failed_stock["outcome"] = "failed_insufficient"
    combined = pd.concat([created, failed_stock], ignore_index=True)
    combined = combined.dropna(subset=["warehouse"])

    grouped = combined.groupby(["date", "warehouse", "outcome"]).size().unstack(fill_value=0)
    for column in ("successful", "failed_insufficient"):
        if column not in grouped.columns:
            grouped[column] = 0

    grouped = grouped.reset_index()
    grouped["total"] = grouped["successful"] + grouped["failed_insufficient"]
    grouped["fulfillment_rate_pct"] = grouped["successful"].div(grouped["total"]).mul(100).round(2)
    grouped.loc[grouped["total"] == 0, "fulfillment_rate_pct"] = None

    return _serialize_records(grouped.sort_values(["date", "warehouse"]))


def compute_stock_discrepancy_frequency(
    session: Session,
    start_date: date,
    end_date: date,
) -> list[dict[str, Any]]:
    df = _load_events(
        session,
        ("direct_stock_edit_rejected",),
        start_date,
        end_date,
    )
    if df.empty:
        return []

    rejections = df[df["event_type"] == "direct_stock_edit_rejected"].dropna(subset=["warehouse"])
    if rejections.empty:
        return []

    daily = (
        rejections.groupby(["date", "warehouse"])
        .size()
        .reset_index(name="rejection_count")
        .sort_values(["date", "warehouse"])
    )
    return _serialize_records(daily)


def compute_receiving_dispatch_cycle_time(
    session: Session,
    start_date: date,
    end_date: date,
) -> list[dict[str, Any]]:
    df = _load_events(
        session,
        ("receiving_order_created", "dispatch_order_created"),
        start_date,
        end_date,
    )
    if df.empty:
        return []

    receiving = df[
        (df["event_type"] == "receiving_order_created")
        & df["sku_id"].notna()
        & df["warehouse"].notna()
    ].copy()
    dispatch = df[
        (df["event_type"] == "dispatch_order_created")
        & df["sku_id"].notna()
        & df["warehouse"].notna()
        & df["quantity"].notna()
    ].copy()

    if receiving.empty or dispatch.empty:
        return []

    receiving = receiving.sort_values(["warehouse", "sku_id", "timestamp"])
    dispatch = dispatch.sort_values(["warehouse", "sku_id", "timestamp"])
    receiving = receiving.rename(columns={"timestamp": "recv_timestamp"})

    merged = pd.merge_asof(
        dispatch,
        receiving[["recv_timestamp", "warehouse", "sku_id", "receiving_order_id"]],
        left_on="timestamp",
        right_on="recv_timestamp",
        by=["warehouse", "sku_id"],
        direction="backward",
    )
    merged = merged.dropna(subset=["recv_timestamp"])
    if merged.empty:
        return []

    merged["cycle_hours"] = (
        merged["timestamp"] - merged["recv_timestamp"]
    ).dt.total_seconds() / 3600.0

    aggregated = (
        merged.groupby(["date", "warehouse"])
        .agg(
            avg_cycle_hours=("cycle_hours", "mean"),
            sample_size=("quantity", "sum"),
        )
        .reset_index()
        .sort_values(["date", "warehouse"])
    )
    aggregated["avg_cycle_hours"] = aggregated["avg_cycle_hours"].round(2)

    return _serialize_records(aggregated)


def build_metrics(
    session: Session,
    start_date: date,
    end_date: date,
) -> dict[str, list[dict[str, Any]]]:
    return {
        "order_fulfillment_rate": compute_fulfillment_rate(session, start_date, end_date),
        "stock_discrepancy_frequency": compute_stock_discrepancy_frequency(
            session, start_date, end_date
        ),
        "receiving_dispatch_cycle_time": compute_receiving_dispatch_cycle_time(
            session, start_date, end_date
        ),
    }
