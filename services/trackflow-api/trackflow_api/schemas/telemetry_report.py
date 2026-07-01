"""Response schemas for GET /telemetry/report."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TelemetryReportPeriod(BaseModel):
    since: str | None = None


class FulfillmentRatePoint(BaseModel):
    date: str
    warehouse: str
    fulfillment_rate_pct: float | None
    successful: int
    failed_insufficient: int


class StockDiscrepancyPoint(BaseModel):
    date: str
    warehouse: str
    rejection_count: int


class CycleTimePoint(BaseModel):
    date: str
    warehouse: str
    avg_cycle_hours: float
    sample_size: int


class TelemetryKpiSeries(BaseModel):
    id: str
    definition: str
    unit: str
    series: list[dict[str, Any]]
    matching_rule: str | None = None


class TelemetryReportResponse(BaseModel):
    generated_at: str
    period: TelemetryReportPeriod
    event_count: int
    kpis: list[TelemetryKpiSeries] = Field(default_factory=list)
