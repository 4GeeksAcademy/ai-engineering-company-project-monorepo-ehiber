"""KPI 3 — receiving-to-dispatch cycle time using FIFO lot matching."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class _ReceivingLot:
    receiving_order_id: int
    timestamp: pd.Timestamp
    quantity_remaining: int


def _match_fifo_cycle_hours(
    receiving: pd.DataFrame,
    dispatch: pd.DataFrame,
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []

    for (warehouse, sku_id), group in pd.concat(
        [
            receiving.assign(kind="receiving"),
            dispatch.assign(kind="dispatch"),
        ],
        ignore_index=True,
    ).groupby(["warehouse", "sku_id"], sort=False):
        ordered = group.sort_values("timestamp")
        queue: deque[_ReceivingLot] = deque()

        for _, row in ordered.iterrows():
            if row["kind"] == "receiving":
                queue.append(
                    _ReceivingLot(
                        receiving_order_id=int(row["receiving_order_id"]),
                        timestamp=row["timestamp"],
                        quantity_remaining=int(row["quantity"]),
                    )
                )
                continue

            remaining = int(row["quantity"])
            dispatch_timestamp = row["timestamp"]
            dispatch_date = row["date"]

            while remaining > 0 and queue:
                lot = queue[0]
                consumed = min(remaining, lot.quantity_remaining)
                cycle_hours = (
                    dispatch_timestamp - lot.timestamp
                ).total_seconds() / 3600.0
                matches.append(
                    {
                        "date": dispatch_date,
                        "warehouse": warehouse,
                        "cycle_hours": cycle_hours,
                        "sample_units": consumed,
                    }
                )
                lot.quantity_remaining -= consumed
                remaining -= consumed
                if lot.quantity_remaining == 0:
                    queue.popleft()

    return matches


def compute_receiving_dispatch_cycle_time(df: pd.DataFrame) -> dict[str, Any]:
    receiving = df[
        (df["event_type"] == "receiving_order_created")
        & df["receiving_order_id"].notna()
        & df["quantity"].notna()
        & df["sku_id"].notna()
        & df["warehouse"].notna()
    ].copy()
    dispatch = df[
        (df["event_type"] == "dispatch_order_created")
        & df["quantity"].notna()
        & df["sku_id"].notna()
        & df["warehouse"].notna()
    ].copy()

    if receiving.empty or dispatch.empty:
        return {
            "id": "receiving_dispatch_cycle_time",
            "definition": (
                "Average hours between a ReceivingOrder and the first DispatchOrder "
                "consuming from the same FIFO lot (sku_id + warehouse)"
            ),
            "unit": "hours",
            "matching_rule": "fifo_by_sku_id_and_warehouse",
            "series": [],
        }

    matches = _match_fifo_cycle_hours(receiving, dispatch)
    if not matches:
        return {
            "id": "receiving_dispatch_cycle_time",
            "definition": (
                "Average hours between a ReceivingOrder and the first DispatchOrder "
                "consuming from the same FIFO lot (sku_id + warehouse)"
            ),
            "unit": "hours",
            "matching_rule": "fifo_by_sku_id_and_warehouse",
            "series": [],
        }

    match_df = pd.DataFrame(matches)
    aggregated = (
        match_df.groupby(["date", "warehouse"])
        .agg(
            avg_cycle_hours=("cycle_hours", "mean"),
            sample_size=("sample_units", "sum"),
        )
        .reset_index()
        .sort_values(["date", "warehouse"])
    )

    series = [
        {
            "date": row["date"].isoformat()
            if hasattr(row["date"], "isoformat")
            else str(row["date"]),
            "warehouse": row["warehouse"],
            "avg_cycle_hours": round(float(row["avg_cycle_hours"]), 2),
            "sample_size": int(row["sample_size"]),
        }
        for _, row in aggregated.iterrows()
    ]

    return {
        "id": "receiving_dispatch_cycle_time",
        "definition": (
            "Average hours between a ReceivingOrder and the first DispatchOrder "
            "consuming from the same FIFO lot (sku_id + warehouse)"
        ),
        "unit": "hours",
        "matching_rule": "fifo_by_sku_id_and_warehouse",
        "series": series,
    }
