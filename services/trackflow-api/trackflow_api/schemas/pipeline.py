"""Schemas for telemetry pipeline run metadata and manual triggers."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class PipelineRunMetadata(BaseModel):
    run_id: str
    pipeline_name: str
    processing_date: str
    status: str
    started_at: str | None
    finished_at: str | None
    records_processed: int = Field(description="Events extracted from telemetry_events")
    metrics_written: int
    events_rejected: int
    error_summary: str | None
    triggered_by: str


class PipelineRunTriggerRequest(BaseModel):
    processing_date: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    force: bool = False


class PipelineRunTriggerResponse(BaseModel):
    pipeline_name: str
    succeeded: int
    skipped: int
    failed: int
    results: list[dict]
