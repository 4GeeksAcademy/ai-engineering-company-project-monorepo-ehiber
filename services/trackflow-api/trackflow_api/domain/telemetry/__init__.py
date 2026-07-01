"""Legacy import path — analysis lives in services/telemetry/analysis.py."""

from telemetry.analysis import (  # noqa: F401
    build_metrics,
    compute_fulfillment_rate,
    compute_receiving_dispatch_cycle_time,
    compute_stock_discrepancy_frequency,
)

__all__ = [
    "build_metrics",
    "compute_fulfillment_rate",
    "compute_stock_discrepancy_frequency",
    "compute_receiving_dispatch_cycle_time",
]
