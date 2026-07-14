"""Persistence for tasks that exhausted all retry attempts."""

from __future__ import annotations

from typing import Any

from sqlmodel import Session, select

from ..models import DeadLetterTask


def record_dead_letter_task(
    session: Session,
    *,
    task_id: str,
    task_name: str,
    attempt_number: int,
    error_message: str,
    payload: dict[str, Any] | None = None,
) -> DeadLetterTask:
    entry = DeadLetterTask(
        task_id=task_id,
        task_name=task_name,
        attempt_number=attempt_number,
        error_message=error_message,
        payload=payload or {},
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


def get_dead_letter_task(session: Session, task_id: str) -> DeadLetterTask | None:
    statement = (
        select(DeadLetterTask)
        .where(DeadLetterTask.task_id == task_id)
        .order_by(DeadLetterTask.created_at.desc())
    )
    return session.exec(statement).first()
