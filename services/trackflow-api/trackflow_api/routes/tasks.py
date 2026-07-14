"""Async task status endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..core.database import get_sql_session
from ..core.security import get_current_user
from ..schemas.tasks import TaskStatusResponse
from ..services.task_queue_service import get_task_status

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get(
    "/{task_id}",
    response_model=TaskStatusResponse,
    dependencies=[Depends(get_current_user)],
)
async def task_status_route(
    task_id: str,
    session: Session = Depends(get_sql_session),
) -> TaskStatusResponse:
    return get_task_status(session, task_id)
