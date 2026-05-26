from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from ..core.errors import AnalysisInputError, ExportUnavailableError
from ..core.security import get_current_user
from ..schemas.incidents_manager import (
    FieldValidationErrorDetail,
    IncidentCreate,
    IncidentPublic,
    IncidentStatusUpdate,
    IncidentSummary,
)
from ..services.incident_manager_service import (
    FieldValidationError,
    create_incident,
    get_incident,
    get_incident_summary,
    list_incidents,
    update_incident_status,
)
from ..services.incidents_service import (
    analyze_uploaded_incidents,
    export_last_analysis_csv,
    get_latest_analysis,
)


router = APIRouter()


@router.post("/analyze", dependencies=[Depends(get_current_user)])
async def analyze_incidents(file: UploadFile = File(...)) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="A CSV file name is required.")

    try:
        payload = await file.read()
        return analyze_uploaded_incidents(file.filename, payload)
    except AnalysisInputError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/results/latest", dependencies=[Depends(get_current_user)])
async def latest_results() -> dict:
    try:
        return get_latest_analysis()
    except ExportUnavailableError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/results/export", dependencies=[Depends(get_current_user)])
async def export_results() -> FileResponse:
    try:
        export_path = export_last_analysis_csv()
    except ExportUnavailableError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return FileResponse(
        path=export_path,
        media_type="text/csv",
        filename="results.csv",
    )


@router.get("/summary", response_model=IncidentSummary, dependencies=[Depends(get_current_user)])
async def incident_summary_route() -> IncidentSummary:
    return get_incident_summary()


@router.post("", response_model=IncidentPublic, status_code=201, dependencies=[Depends(get_current_user)])
async def create_incident_route(payload: IncidentCreate) -> IncidentPublic:
    try:
        return create_incident(payload)
    except FieldValidationError as exc:
        raise _validation_http_error(exc) from exc


@router.get("", response_model=list[IncidentPublic], dependencies=[Depends(get_current_user)])
async def list_incidents_route(
    status: str | None = Query(default=None),
    origin: str | None = Query(default=None),
    branch: str | None = Query(default=None),
    category: str | None = Query(default=None),
) -> list[IncidentPublic]:
    try:
        return list_incidents(status=status, origin=origin, branch=branch, category=category)
    except FieldValidationError as exc:
        raise _validation_http_error(exc) from exc


@router.get("/{incident_id}", response_model=IncidentPublic, dependencies=[Depends(get_current_user)])
async def get_incident_route(incident_id: int) -> IncidentPublic:
    incident = get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found.")
    return incident


@router.patch("/{incident_id}/status", response_model=IncidentPublic, dependencies=[Depends(get_current_user)])
async def update_incident_status_route(
    incident_id: int,
    payload: IncidentStatusUpdate,
) -> IncidentPublic:
    try:
        return update_incident_status(incident_id, payload)
    except FieldValidationError as exc:
        raise _validation_http_error(exc) from exc


def _validation_http_error(exc: FieldValidationError) -> HTTPException:
    return HTTPException(
        status_code=400,
        detail=FieldValidationErrorDetail(field=exc.field, message=exc.message).model_dump(),
    )
