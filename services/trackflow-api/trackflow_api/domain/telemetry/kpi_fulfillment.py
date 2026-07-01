"""KPI 1 — order fulfillment rate (dispatch success vs insufficient_stock failures)."""

from __future__ import annotations

from typing import Any

import pandas as pd


def compute_fulfillment_rate(df: pd.DataFrame) -> dict[str, Any]:
    created = df[df["event_type"] == "dispatch_order_created"].copy()
    failed_stock = df[
        (df["event_type"] == "dispatch_order_failed")
        & (df["failure_reason"] == "insufficient_stock")
    ].copy()

    if created.empty and failed_stock.empty:
        return {
            "id": "order_fulfillment_rate",
            "definition": (
                "Successful dispatches / (successful + insufficient_stock failures)"
            ),
            "unit": "percent",
            "series": [],
        }

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
    grouped["fulfillment_rate_pct"] = grouped.apply(
        lambda row: round((row["successful"] / row["total"]) * 100, 2)
        if row["total"] > 0
        else None,
        axis=1,
    )

    series = [
        {
            "date": row["date"].isoformat(),
            "warehouse": row["warehouse"],
            "fulfillment_rate_pct": row["fulfillment_rate_pct"],
            "successful": int(row["successful"]),
            "failed_insufficient": int(row["failed_insufficient"]),
        }
        for _, row in grouped.sort_values(["date", "warehouse"]).iterrows()
    ]

    return {
        "id": "order_fulfillment_rate",
        "definition": (
            "Successful dispatches / (successful + insufficient_stock failures)"
        ),
        "unit": "percent",
        "series": series,
    }
