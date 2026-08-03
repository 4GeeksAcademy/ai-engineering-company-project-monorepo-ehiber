"""Celery task for RFP Parte 1 intake analysis."""

from __future__ import annotations

from typing import Any

from celery.exceptions import SoftTimeLimitExceeded
from sqlmodel import Session

from ..core.celery_app import celery_app
from ..core.config import get_settings
from ..core.database import get_inventory_engine, init_inventory_db
from ..repositories.dead_letter_repository import record_dead_letter_task
from ..services.rfp_service import process_rfp_ticket

RFP_INTAKE_TASK_NAME = "trackflow_api.tasks.rfp.run_rfp_intake_task"


def _record_dlq(
    *,
    task_id: str,
    attempt_number: int,
    error_message: str,
    payload: dict[str, Any],
) -> None:
    init_inventory_db()
    with Session(get_inventory_engine()) as session:
        record_dead_letter_task(
            session,
            task_id=task_id,
            task_name=RFP_INTAKE_TASK_NAME,
            attempt_number=attempt_number,
            error_message=error_message,
            payload=payload,
        )


@celery_app.task(
    bind=True,
    name=RFP_INTAKE_TASK_NAME,
    max_retries=None,
)
def run_rfp_intake_task(self, payload: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    ticket_id = str(payload.get("ticket_id") or "")
    if not ticket_id:
        raise ValueError("payload.ticket_id is required")

    try:
        init_inventory_db()
        with Session(get_inventory_engine()) as session:
            ticket = process_rfp_ticket(session, ticket_id)
            return {
                "ticket_id": ticket_id,
                "status": ticket.status,
                "is_rfp": ticket.is_rfp,
            }
    except SoftTimeLimitExceeded as exc:
        attempt = int(self.request.retries) + 1
        if attempt > settings.celery_task_max_retries:
            _record_dlq(
                task_id=str(self.request.id),
                attempt_number=attempt,
                error_message=str(exc),
                payload=payload,
            )
            raise
        raise self.retry(exc=exc, countdown=2**attempt) from exc
    except Exception as exc:  # noqa: BLE001
        attempt = int(self.request.retries) + 1
        if attempt > settings.celery_task_max_retries:
            _record_dlq(
                task_id=str(self.request.id),
                attempt_number=attempt,
                error_message=str(exc),
                payload=payload,
            )
            raise
        raise self.retry(exc=exc, countdown=2**attempt) from exc
