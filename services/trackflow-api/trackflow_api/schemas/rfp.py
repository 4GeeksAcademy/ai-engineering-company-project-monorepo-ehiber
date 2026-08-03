"""Pydantic schemas for RFP ticket API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DepartmentSectionRead(BaseModel):
    department_id: str
    key_aspects: list[str] = Field(default_factory=list)
    draft_content: str | None = None
    evaluation_results: dict[str, Any] = Field(default_factory=dict)
    approval_status: str
    approver: str
    approved_at: datetime | None = None
    iteration_count: int = 0


class RfpTicketSummary(BaseModel):
    ticket_id: str
    rfp_id: str
    status: str
    original_filename: str
    client_name: str | None = None
    client_country: str | None = None
    is_rfp: bool | None = None
    departments_needed: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class RfpTicketDetail(RfpTicketSummary):
    approval_phase: str | None = None
    classifier_reason: str | None = None
    services_requested: list[str] = Field(default_factory=list)
    monthly_volume: int | None = None
    deadline: str | None = None
    budget_range: str | None = None
    readability_metrics: dict[str, Any] = Field(default_factory=dict)
    processing_cost_estimate: dict[str, Any] = Field(default_factory=dict)
    synthesis_brief: str | None = None
    markdown_preview: str | None = None
    error_message: str | None = None
    celery_task_id: str | None = None
    sections: list[DepartmentSectionRead] = Field(default_factory=list)


class RfpTicketCreateResponse(BaseModel):
    ticket_id: str
    rfp_id: str
    status: str
    celery_task_id: str | None = None


class ApproveIntakeResponse(BaseModel):
    ticket_id: str
    status: str
    message: str
