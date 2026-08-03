"""RFP ticket intake service: upload, enqueue, process Parte 1 graph."""

from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path

from sqlmodel import Session

from ..core.config import REPO_ROOT, get_settings
from ..models import RfpTicket
from ..repositories import rfp_repository
from ..rfp.graph import run_rfp_part1
from ..rfp.ingest import pdf_bytes_to_markdown
from ..schemas.rfp import (
    ApproveIntakeResponse,
    DepartmentSectionRead,
    RfpTicketCreateResponse,
    RfpTicketDetail,
    RfpTicketSummary,
)

logger = logging.getLogger(__name__)


def _storage_root() -> Path:
    settings = get_settings()
    configured = getattr(settings, "rfp_storage_dir", None) or "data/rfp/uploads"
    path = Path(configured)
    if not path.is_absolute():
        path = REPO_ROOT / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def _use_llm() -> bool:
    settings = get_settings()
    if not settings.litellm_api_key:
        return False
    return os.getenv("RFP_USE_LLM", "").strip() in {"1", "true", "True"}


def ticket_to_summary(ticket: RfpTicket) -> RfpTicketSummary:
    return RfpTicketSummary(
        ticket_id=ticket.ticket_id,
        rfp_id=ticket.rfp_id,
        status=ticket.status,
        original_filename=ticket.original_filename,
        client_name=ticket.client_name,
        client_country=ticket.client_country,
        is_rfp=ticket.is_rfp,
        departments_needed=list(ticket.departments_needed or []),
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )


def ticket_to_detail(session: Session, ticket: RfpTicket) -> RfpTicketDetail:
    sections = rfp_repository.list_sections(session, ticket.ticket_id)
    preview = None
    if ticket.markdown_content:
        preview = ticket.markdown_content[:2000]
    return RfpTicketDetail(
        **ticket_to_summary(ticket).model_dump(),
        approval_phase=ticket.approval_phase,
        classifier_reason=ticket.classifier_reason,
        services_requested=list(ticket.services_requested or []),
        monthly_volume=ticket.monthly_volume,
        deadline=ticket.deadline,
        budget_range=ticket.budget_range,
        readability_metrics=dict(ticket.readability_metrics or {}),
        processing_cost_estimate=dict(ticket.processing_cost_estimate or {}),
        synthesis_brief=ticket.synthesis_brief,
        markdown_preview=preview,
        error_message=ticket.error_message,
        celery_task_id=ticket.celery_task_id,
        sections=[
            DepartmentSectionRead(
                department_id=s.department_id,
                key_aspects=list(s.key_aspects or []),
                draft_content=s.draft_content,
                evaluation_results=dict(s.evaluation_results or {}),
                approval_status=s.approval_status,
                approver=s.approver,
                approved_at=s.approved_at,
                iteration_count=s.iteration_count,
            )
            for s in sections
        ],
    )


def create_ticket_from_upload(
    session: Session,
    *,
    filename: str,
    pdf_bytes: bytes,
    user_uuid: str | None,
) -> RfpTicketCreateResponse:
    ticket_id = str(uuid.uuid4())
    rfp_id = f"rfp_{ticket_id[:8]}"
    safe_name = Path(filename).name or "upload.pdf"
    dest = _storage_root() / ticket_id
    dest.mkdir(parents=True, exist_ok=True)
    pdf_path = dest / safe_name
    pdf_path.write_bytes(pdf_bytes)

    ticket = rfp_repository.create_ticket(
        session,
        ticket_id=ticket_id,
        rfp_id=rfp_id,
        original_filename=safe_name,
        pdf_path=str(pdf_path),
        created_by_user_uuid=user_uuid,
    )

    task_id: str | None = None
    try:
        from ..tasks.rfp import run_rfp_intake_task

        async_result = run_rfp_intake_task.delay({"ticket_id": ticket_id})
        task_id = async_result.id
        ticket = rfp_repository.update_ticket_fields(session, ticket, celery_task_id=task_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Celery enqueue failed for RFP %s; running inline: %s", ticket_id, exc)
        ticket = process_rfp_ticket(session, ticket_id)

    # Eager mode (or inline) may already have finished Parte 1.
    session.refresh(ticket)

    return RfpTicketCreateResponse(
        ticket_id=ticket_id,
        rfp_id=rfp_id,
        status=ticket.status,
        celery_task_id=task_id,
    )


def process_rfp_ticket(session: Session, ticket_id: str) -> RfpTicket:
    ticket = rfp_repository.get_ticket(session, ticket_id)
    if ticket is None:
        raise ValueError(f"Unknown ticket_id={ticket_id}")

    try:
        pdf_bytes = Path(ticket.pdf_path).read_bytes()
        markdown = pdf_bytes_to_markdown(pdf_bytes, filename=ticket.original_filename)
        md_path = Path(ticket.pdf_path).with_suffix(".md")
        md_path.write_text(markdown, encoding="utf-8")

        result = run_rfp_part1(
            ticket_id=ticket_id,
            markdown=markdown,
            use_llm=_use_llm(),
        )

        metadata = result.get("metadata") or {}
        is_rfp = bool(result.get("is_rfp"))
        status = str(result.get("status") or ("esperando_aprobación" if is_rfp else "descartado"))

        rfp_repository.update_ticket_fields(
            session,
            ticket,
            markdown_path=str(md_path),
            markdown_content=markdown,
            is_rfp=is_rfp,
            classifier_reason=result.get("classifier_reason"),
            client_name=metadata.get("client_name"),
            client_country=metadata.get("client_country"),
            services_requested=list(metadata.get("services_requested") or []),
            monthly_volume=metadata.get("monthly_volume"),
            deadline=metadata.get("deadline"),
            budget_range=metadata.get("budget_range"),
            departments_needed=list(metadata.get("departments_needed") or []),
            readability_metrics=dict(result.get("readability_metrics") or {}),
            processing_cost_estimate=dict(result.get("processing_cost_estimate") or {}),
            synthesis_brief=result.get("synthesis_brief"),
            status=status,
            approval_phase="intake" if is_rfp else None,
            error_message=None,
        )

        if is_rfp:
            rfp_repository.replace_sections(
                session,
                ticket_id=ticket_id,
                sections=list(result.get("worker_results") or []),
            )
        return rfp_repository.get_ticket(session, ticket_id) or ticket
    except Exception as exc:  # noqa: BLE001
        logger.exception("RFP processing failed for %s", ticket_id)
        return rfp_repository.update_ticket_fields(
            session,
            ticket,
            status="descartado",
            error_message=str(exc),
        )


def approve_intake(session: Session, ticket_id: str) -> ApproveIntakeResponse:
    ticket = rfp_repository.get_ticket(session, ticket_id)
    if ticket is None:
        raise ValueError("Ticket not found")
    if ticket.status != "esperando_aprobación" or ticket.approval_phase != "intake":
        raise ValueError("Ticket is not waiting for intake approval")
    # Parte 2 stub: mark ready for draft generation without running generators yet.
    rfp_repository.update_ticket_fields(
        session,
        ticket,
        status="generando_borrador",
        approval_phase=None,
    )
    return ApproveIntakeResponse(
        ticket_id=ticket_id,
        status="generando_borrador",
        message=(
            "Intake aprobado. El ticket queda en generando_borrador "
            "(generación de secciones = Parte 2)."
        ),
    )


def list_ticket_summaries(session: Session) -> list[RfpTicketSummary]:
    return [ticket_to_summary(t) for t in rfp_repository.list_tickets(session)]
