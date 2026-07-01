"""Response schemas for GET /telemetry/report."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TelemetryReportPeriod(BaseModel):
    start_date: str
    end_date: str


class TelemetryReportResponse(BaseModel):
    period: TelemetryReportPeriod
    metrics: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
