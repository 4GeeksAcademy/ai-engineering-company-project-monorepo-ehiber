"""Schemas for async task queue status endpoints."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


TaskStatus = Literal["pending", "started", "success", "failure", "dead_letter"]


class TaskAcceptedResponse(BaseModel):
    task_id: str
    status: Literal["pending"] = "pending"


class TaskStatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    result: dict[str, Any] | None = None
    error: str | None = None
    attempt_number: int | None = Field(
        default=None,
        description="Present when the task landed in the dead letter queue.",
    )
