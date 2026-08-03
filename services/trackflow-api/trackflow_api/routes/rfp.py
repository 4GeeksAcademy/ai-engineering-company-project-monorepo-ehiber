"""RFP ticket-mode API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session

from ..core.database import get_sql_session
from ..core.security import get_current_user
from ..repositories import rfp_repository
from ..schemas.rfp import (
    ApproveIntakeResponse,
    RfpTicketCreateResponse,
    RfpTicketDetail,
    RfpTicketSummary,
)
from ..schemas.users import UserPublic
from ..services import rfp_service

router = APIRouter(prefix="/api/rfp", tags=["rfp"])


@router.post("/tickets", response_model=RfpTicketCreateResponse, status_code=202)
async def create_rfp_ticket(
    current_user: Annotated[UserPublic, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_sql_session)],
    file: UploadFile = File(...),
) -> RfpTicketCreateResponse:
    filename = file.filename or "upload.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF.")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="El archivo está vacío.")
    try:
        return rfp_service.create_ticket_from_upload(
            session,
            filename=filename,
            pdf_bytes=content,
            user_uuid=current_user.user_uuid,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"No se pudo crear el ticket: {exc}") from exc


@router.get("/tickets", response_model=list[RfpTicketSummary])
def list_rfp_tickets(
    current_user: Annotated[UserPublic, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_sql_session)],
) -> list[RfpTicketSummary]:
    _ = current_user
    return rfp_service.list_ticket_summaries(session)


@router.get("/tickets/{ticket_id}", response_model=RfpTicketDetail)
def get_rfp_ticket(
    ticket_id: str,
    current_user: Annotated[UserPublic, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_sql_session)],
) -> RfpTicketDetail:
    _ = current_user
    ticket = rfp_repository.get_ticket(session, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket no encontrado.")
    return rfp_service.ticket_to_detail(session, ticket)


@router.post("/tickets/{ticket_id}/approve-intake", response_model=ApproveIntakeResponse)
def approve_rfp_intake(
    ticket_id: str,
    current_user: Annotated[UserPublic, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_sql_session)],
) -> ApproveIntakeResponse:
    _ = current_user
    try:
        return rfp_service.approve_intake(session, ticket_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
