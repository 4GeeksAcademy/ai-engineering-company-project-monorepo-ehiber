"""KPI 2 — direct stock edit rejection frequency by warehouse and day."""

from __future__ import annotations

from typing import Any

import pandas as pd


def compute_stock_discrepancy_frequency(df: pd.DataFrame) -> dict[str, Any]:
    rejections = df[df["event_type"] == "direct_stock_edit_rejected"].copy()
    rejections = rejections.dropna(subset=["warehouse"])

    if rejections.empty:
        return {
            "id": "stock_discrepancy_frequency",
            "definition": "Count of direct stock edit attempts rejected by the API",
            "unit": "count",
            "series": [],
        }

    daily = (
        rejections.groupby(["date", "warehouse"])
        .size()
        .reset_index(name="rejection_count")
        .sort_values(["date", "warehouse"])
    )

    series = [
        {
            "date": row["date"].isoformat(),
            "warehouse": row["warehouse"],
            "rejection_count": int(row["rejection_count"]),
        }
        for _, row in daily.iterrows()
    ]

    return {
        "id": "stock_discrepancy_frequency",
        "definition": "Count of direct stock edit attempts rejected by the API",
        "unit": "count",
        "series": series,
    }
