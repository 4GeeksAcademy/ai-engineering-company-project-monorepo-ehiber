"""Celery tasks for long-running API operations."""

from __future__ import annotations

from datetime import date
from typing import Any

from celery.exceptions import SoftTimeLimitExceeded
from sqlmodel import Session

from ..core.celery_app import celery_app
from ..core.config import get_settings
from ..core.database import get_inventory_engine, init_inventory_db
from ..repositories.dead_letter_repository import record_dead_letter_task
from ..services.pipeline_trigger_service import run_telemetry_pipeline_direct_job

PIPELINE_TASK_NAME = "trackflow_api.tasks.pipeline.run_telemetry_pipeline_task"


def _parse_optional_date(value: str | None) -> date | None:
    if value is None:
        return None
    return date.fromisoformat(value)


def record_pipeline_task_dlq(
    *,
    task_id: str,
    task_name: str,
    attempt_number: int,
    error_message: str,
    payload: dict[str, Any],
) -> None:
    init_inventory_db()
    with Session(get_inventory_engine()) as session:
        record_dead_letter_task(
            session,
            task_id=task_id,
            task_name=task_name,
            attempt_number=attempt_number,
            error_message=error_message,
            payload=payload,
        )


@celery_app.task(
    bind=True,
    name=PIPELINE_TASK_NAME,
    max_retries=None,
)
def run_telemetry_pipeline_task(self, payload: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    max_attempts = settings.celery_task_max_retries + 1
    attempt_number = self.request.retries + 1

    try:
        init_inventory_db()
        return run_telemetry_pipeline_direct_job(
            processing_date=_parse_optional_date(payload.get("processing_date")),
            start_date=_parse_optional_date(payload.get("start_date")),
            end_date=_parse_optional_date(payload.get("end_date")),
            force=bool(payload.get("force", False)),
            triggered_by=str(payload.get("triggered_by", "celery-worker")),
        )
    except (Exception, SoftTimeLimitExceeded) as exc:
        if attempt_number >= max_attempts:
            record_pipeline_task_dlq(
                task_id=self.request.id,
                task_name=self.name,
                attempt_number=attempt_number,
                error_message=str(exc),
                payload=payload,
            )
            raise

        raise self.retry(exc=exc, countdown=60)
