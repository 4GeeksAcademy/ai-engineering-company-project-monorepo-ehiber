from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ...core.errors import AnalysisInputError, ExportUnavailableError
from ...core.security import get_current_user
from ...services.incidents_service import (
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
