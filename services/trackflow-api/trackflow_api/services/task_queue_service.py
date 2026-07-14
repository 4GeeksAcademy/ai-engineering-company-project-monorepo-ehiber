"""Enqueue and inspect Celery background tasks."""

from __future__ import annotations

from datetime import date
from typing import Any

from celery.result import AsyncResult
from sqlmodel import Session

from ..core.celery_app import celery_app
from ..repositories.dead_letter_repository import get_dead_letter_task
from ..schemas.tasks import TaskAcceptedResponse, TaskStatusResponse
from ..tasks.pipeline import run_telemetry_pipeline_task


def _serialize_trigger_payload(
    *,
    processing_date: date | None,
    start_date: date | None,
    end_date: date | None,
    force: bool,
    triggered_by: str,
) -> dict[str, Any]:
    return {
        "processing_date": processing_date.isoformat() if processing_date else None,
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "force": force,
        "triggered_by": triggered_by,
    }


def enqueue_telemetry_pipeline_run(
    *,
    processing_date: date | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    force: bool = False,
    triggered_by: str = "manual",
) -> TaskAcceptedResponse:
    payload = _serialize_trigger_payload(
        processing_date=processing_date,
        start_date=start_date,
        end_date=end_date,
        force=force,
        triggered_by=triggered_by,
    )
    async_result = run_telemetry_pipeline_task.delay(payload)
    return TaskAcceptedResponse(task_id=async_result.id)


def get_task_status(session: Session, task_id: str) -> TaskStatusResponse:
    dead_letter = get_dead_letter_task(session, task_id)
    if dead_letter is not None:
        return TaskStatusResponse(
            task_id=task_id,
            status="dead_letter",
            error=dead_letter.error_message,
            attempt_number=dead_letter.attempt_number,
        )

    result = AsyncResult(task_id, app=celery_app)
    state = result.state

    if state == "PENDING":
        return TaskStatusResponse(task_id=task_id, status="pending")
    if state == "STARTED":
        return TaskStatusResponse(task_id=task_id, status="started")
    if state == "SUCCESS":
        payload = result.result
        return TaskStatusResponse(
            task_id=task_id,
            status="success",
            result=payload if isinstance(payload, dict) else {"value": payload},
        )
    if state == "FAILURE":
        return TaskStatusResponse(
            task_id=task_id,
            status="failure",
            error=str(result.result),
        )

    return TaskStatusResponse(task_id=task_id, status="pending")
