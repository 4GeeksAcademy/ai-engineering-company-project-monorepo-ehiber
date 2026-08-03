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
    ArbitrationRequest,
    RfpTicketCreateResponse,
    RfpTicketDetail,
    RfpTicketSummary,
    SectionDecisionRequest,
    SectionDecisionResponse,
    TraceListResponse,
    TraceEntryRead,
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


@router.get("/tickets/{ticket_id}/trace", response_model=TraceListResponse)
def get_rfp_trace(
    ticket_id: str,
    current_user: Annotated[UserPublic, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_sql_session)],
) -> TraceListResponse:
    _ = current_user
    ticket = rfp_repository.get_ticket(session, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket no encontrado.")
    items = [
        TraceEntryRead(
            timestamp=str(item.get("timestamp")),
            agent=str(item.get("agent")),
            input=item.get("input"),
            output=item.get("output"),
            part=item.get("part"),
            department_id=item.get("department_id"),
        )
        for item in (ticket.run_trace or [])
        if isinstance(item, dict)
    ]
    return TraceListResponse(ticket_id=ticket_id, items=items)


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


@router.post(
    "/tickets/{ticket_id}/sections/{department_id}/approve",
    response_model=SectionDecisionResponse,
)
def approve_section(
    ticket_id: str,
    department_id: str,
    current_user: Annotated[UserPublic, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_sql_session)],
    payload: SectionDecisionRequest | None = None,
) -> SectionDecisionResponse:
    _ = current_user
    try:
        return rfp_service.decide_section(
            session,
            ticket_id,
            department_id,
            action="approve",
            comment=(payload.comment if payload else None),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/tickets/{ticket_id}/sections/{department_id}/reject",
    response_model=SectionDecisionResponse,
)
def reject_section(
    ticket_id: str,
    department_id: str,
    current_user: Annotated[UserPublic, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_sql_session)],
    payload: SectionDecisionRequest | None = None,
) -> SectionDecisionResponse:
    _ = current_user
    try:
        return rfp_service.decide_section(
            session,
            ticket_id,
            department_id,
            action="reject",
            comment=(payload.comment if payload else None),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/tickets/{ticket_id}/sections/{department_id}/arbitrate",
    response_model=SectionDecisionResponse,
)
def arbitrate_section(
    ticket_id: str,
    department_id: str,
    payload: ArbitrationRequest,
    current_user: Annotated[UserPublic, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_sql_session)],
) -> SectionDecisionResponse:
    _ = current_user
    action = payload.action.strip().lower()
    if action not in {"force_approve", "force_reject", "discard_ticket"}:
        raise HTTPException(status_code=400, detail="Acción de arbitración inválida.")
    try:
        return rfp_service.arbitrate_section(
            session,
            ticket_id,
            department_id,
            action=action,
            comment=payload.comment,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
