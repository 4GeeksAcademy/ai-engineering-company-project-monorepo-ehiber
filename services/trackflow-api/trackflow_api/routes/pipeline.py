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
    PipelineRunTriggerResponse,
)
from ..services.pipeline_trigger_service import trigger_telemetry_kpi_daily_flow

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
    response_model=PipelineRunTriggerResponse,
    dependencies=[Depends(get_current_user)],
)
async def trigger_pipeline_run(body: PipelineRunTriggerRequest) -> dict:
    """Trigger a manual telemetry KPI pipeline run (imports flow from data/pipelines)."""
    summary = trigger_telemetry_kpi_daily_flow(
        processing_date=body.processing_date,
        start_date=body.start_date,
        end_date=body.end_date,
        force=body.force,
    )
    return {
        "pipeline_name": summary["pipeline_name"],
        "succeeded": summary["succeeded"],
        "skipped": summary["skipped"],
        "failed": summary["failed"],
        "results": summary["results"],
    }
