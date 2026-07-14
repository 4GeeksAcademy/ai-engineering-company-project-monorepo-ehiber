"""Telemetry KPI pipeline observability and manual trigger endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from ..core.database import get_sql_session
from ..core.security import get_current_user
from ..repositories.pipeline_repository import get_latest_run, run_to_metadata
from ..schemas.pipeline import (
    PipelineRunMetadata,
    PipelineRunTriggerRequest,
)
from ..schemas.tasks import TaskAcceptedResponse
from ..services.task_queue_service import enqueue_telemetry_pipeline_run

router = APIRouter(prefix="/telemetry/pipeline", tags=["telemetry-pipeline"])


@router.get(
    "/runs/latest",
    response_model=PipelineRunMetadata,
    dependencies=[Depends(get_current_user)],
)
async def latest_pipeline_run(session: Session = Depends(get_sql_session)) -> dict:
    """Return metadata for the most recent telemetry KPI pipeline run."""
    run = get_latest_run(session)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pipeline runs recorded yet.",
        )
    return run_to_metadata(run)


@router.post(
    "/run",
    response_model=TaskAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(get_current_user)],
)
async def trigger_pipeline_run(body: PipelineRunTriggerRequest) -> TaskAcceptedResponse:
    """Enqueue a telemetry KPI pipeline run and return immediately."""
    return enqueue_telemetry_pipeline_run(
        processing_date=body.processing_date,
        start_date=body.start_date,
        end_date=body.end_date,
        force=body.force,
        triggered_by="manual",
    )
