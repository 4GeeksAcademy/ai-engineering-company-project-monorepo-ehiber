"""RFP ticket intake + Parte 2 generation/evaluation service."""

from __future__ import annotations

import logging
import os
import threading
import uuid
from pathlib import Path
from typing import Any

from sqlmodel import Session

from ..core.config import REPO_ROOT, get_settings
from ..core.database import get_inventory_engine
from ..models import RfpTicket
from ..repositories import rfp_repository
from ..rfp.graph import run_rfp_part1
from ..rfp.ingest import pdf_bytes_to_markdown
from ..rfp.part2 import run_part2_for_departments
from ..schemas.rfp import (
    ApproveIntakeResponse,
    DepartmentSectionRead,
    FinalDocumentRead,
    RfpTicketCreateResponse,
    RfpTicketDetail,
    RfpTicketSummary,
    SectionDecisionResponse,
    TraceEntryRead,
)

logger = logging.getLogger(__name__)
_ticket_locks: dict[str, threading.Lock] = {}
_ticket_locks_guard = threading.Lock()


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


def _lock_for(ticket_id: str) -> threading.Lock:
    with _ticket_locks_guard:
        if ticket_id not in _ticket_locks:
            _ticket_locks[ticket_id] = threading.Lock()
        return _ticket_locks[ticket_id]


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
    final_doc = rfp_repository.get_final_document(session, ticket.ticket_id)
    final_read = None
    if final_doc is not None:
        final_read = FinalDocumentRead(
            ticket_id=final_doc.ticket_id,
            content=final_doc.content,
            currency=final_doc.currency,
            sections=list(final_doc.sections or []),
            generated_at=final_doc.generated_at,
        )
    elif ticket.final_document_content:
        final_read = FinalDocumentRead(
            ticket_id=ticket.ticket_id,
            content=ticket.final_document_content,
            currency=ticket.final_document_currency or "USD",
            sections=list(ticket.departments_needed or []),
            generated_at=ticket.final_document_generated_at or ticket.updated_at,
        )

    pending: list[dict[str, Any]] = []
    if ticket.approval_phase == "section_signoff":
        pending = list_pending_interrupts(ticket.ticket_id, [s.department_id for s in sections])

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
                human_approval_rounds=getattr(s, "human_approval_rounds", 0) or 0,
            )
            for s in sections
        ],
        run_trace=[
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
        ],
        final_document=final_read,
        pending_interrupts=pending,
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


def _ticket_metadata(ticket: RfpTicket) -> dict[str, Any]:
    return {
        "client_name": ticket.client_name,
        "client_country": ticket.client_country,
        "services_requested": list(ticket.services_requested or []),
        "monthly_volume": ticket.monthly_volume,
        "deadline": ticket.deadline,
        "budget_range": ticket.budget_range,
        "departments_needed": list(ticket.departments_needed or []),
    }


def process_rfp_part2(session: Session, ticket_id: str) -> RfpTicket:
    """Run generator–evaluator loops for all active departments and persist handoff for Parte 3."""
    ticket = rfp_repository.get_ticket(session, ticket_id)
    if ticket is None:
        raise ValueError(f"Unknown ticket_id={ticket_id}")

    sections = rfp_repository.list_sections(session, ticket_id)
    if not sections:
        raise ValueError("Ticket has no department sections to generate")

    metadata = _ticket_metadata(ticket)
    markdown = ticket.markdown_content or ""
    sections_by_dept = {s.department_id: list(s.key_aspects or []) for s in sections}
    department_ids = [s.department_id for s in sections]
    lock = _lock_for(ticket_id)

    def on_progress(department_id: str, payload: dict[str, Any]) -> None:
        with lock:
            with Session(get_inventory_engine()) as progress_session:
                t = rfp_repository.get_ticket(progress_session, ticket_id)
                section = rfp_repository.get_section(
                    progress_session, ticket_id=ticket_id, department_id=department_id
                )
                if t is None or section is None:
                    return
                ticket_status = payload.get("ticket_status")
                if ticket_status in {"generando_borrador", "en_evaluación"}:
                    rfp_repository.update_ticket_fields(
                        progress_session, t, status=str(ticket_status)
                    )
                fields: dict[str, Any] = {
                    "evaluation_results": {
                        **dict(section.evaluation_results or {}),
                        "stage": payload.get("stage"),
                        "iteration": payload.get("iteration"),
                    },
                }
                if payload.get("draft_content") is not None:
                    fields["draft_content"] = payload["draft_content"]
                if payload.get("evaluation_results") is not None:
                    fields["evaluation_results"] = payload["evaluation_results"]
                if payload.get("approval_status") is not None:
                    fields["approval_status"] = payload["approval_status"]
                if payload.get("iteration") is not None:
                    fields["iteration_count"] = int(payload["iteration"])
                rfp_repository.update_section_fields(progress_session, section, **fields)

    rfp_repository.update_ticket_fields(
        session, ticket, status="generando_borrador", approval_phase=None, error_message=None
    )

    try:
        results = run_part2_for_departments(
            department_ids,
            metadata=metadata,
            sections_by_dept=sections_by_dept,
            markdown=markdown,
            on_progress=on_progress,
        )

        with lock:
            for result in results:
                section = rfp_repository.get_section(
                    session, ticket_id=ticket_id, department_id=result.department_id
                )
                if section is None:
                    continue
                rfp_repository.update_section_fields(
                    session,
                    section,
                    draft_content=result.draft_content,
                    evaluation_results=result.evaluation_results,
                    iteration_count=result.iteration_count,
                    approval_status=result.approval_status,
                )

            ticket = rfp_repository.get_ticket(session, ticket_id) or ticket
            rfp_repository.update_ticket_fields(
                session,
                ticket,
                status="esperando_aprobación",
                approval_phase="section_signoff",
                error_message=None,
            )
        # Parte 3: start independent HITL interrupts per department (non-blocking).
        return start_part3_approvals(session, ticket_id)
    except Exception as exc:  # noqa: BLE001
        logger.exception("RFP Parte 2 failed for %s", ticket_id)
        ticket = rfp_repository.get_ticket(session, ticket_id) or ticket
        return rfp_repository.update_ticket_fields(
            session,
            ticket,
            status="esperando_aprobación",
            approval_phase="section_signoff",
            error_message=f"Parte 2 error: {exc}",
        )


def list_pending_interrupts(ticket_id: str, department_ids: list[str]) -> list[dict[str, Any]]:
    from ..rfp.part3 import department_thread_id, get_compiled_dept_approval_graph

    graph = get_compiled_dept_approval_graph()
    pending: list[dict[str, Any]] = []
    for dept_id in department_ids:
        config = {"configurable": {"thread_id": department_thread_id(ticket_id, dept_id)}}
        try:
            state = graph.get_state(config)
        except Exception:  # noqa: BLE001
            continue
        for task in state.tasks:
            for item in getattr(task, "interrupts", None) or []:
                value = getattr(item, "value", item)
                if isinstance(value, dict):
                    pending.append(value)
    return pending


def start_part3_approvals(session: Session, ticket_id: str) -> RfpTicket:
    """Pause each department branch independently at human approval."""
    from ..rfp.part3 import start_department_approval
    from ..rfp.trace import make_trace_entry

    ticket = rfp_repository.get_ticket(session, ticket_id)
    if ticket is None:
        raise ValueError(f"Unknown ticket_id={ticket_id}")

    sections = rfp_repository.list_sections(session, ticket_id)
    metadata = _ticket_metadata(ticket)
    entries = [
        make_trace_entry(
            agent="start_part3",
            input_payload={"ticket_id": ticket_id, "departments": [s.department_id for s in sections]},
            output_payload={"phase": "section_signoff"},
            part=3,
        )
    ]

    for section in sections:
        if section.approval_status == "approved":
            continue
        # Reset to pending for human sign-off (eval may have left needs_human_review).
        if section.approval_status not in {"pending", "needs_arbitration"}:
            rfp_repository.update_section_fields(
                session, section, approval_status="pending"
            )
        result = start_department_approval(
            ticket_id=ticket_id,
            department_id=section.department_id,
            draft_content=section.draft_content or "",
            key_aspects=list(section.key_aspects or []),
            metadata=metadata,
            human_approval_rounds=int(section.human_approval_rounds or 0),
        )
        values = result.get("values") or {}
        logs = list(values.get("node_logs") or [])
        entries.extend(logs)
        entries.append(
            make_trace_entry(
                agent="part3_interrupt",
                input_payload={"department_id": section.department_id},
                output_payload={
                    "interrupted": result.get("interrupted"),
                    "interrupts": result.get("interrupts"),
                },
                part=3,
                department_id=section.department_id,
            )
        )

    ticket = rfp_repository.get_ticket(session, ticket_id) or ticket
    rfp_repository.append_ticket_trace(session, ticket, entries)
    ticket = rfp_repository.get_ticket(session, ticket_id) or ticket
    return rfp_repository.update_ticket_fields(
        session,
        ticket,
        status="esperando_aprobación",
        approval_phase="section_signoff",
    )


def _maybe_assemble_final(session: Session, ticket_id: str) -> RfpTicket:
    from datetime import datetime, timezone

    from ..rfp.final_document import assemble_final_document
    from ..rfp.trace import make_trace_entry

    ticket = rfp_repository.get_ticket(session, ticket_id)
    if ticket is None:
        raise ValueError("Ticket not found")
    sections = rfp_repository.list_sections(session, ticket_id)
    if not sections:
        return ticket
    if any(s.approval_status != "approved" for s in sections):
        return ticket

    assembled = assemble_final_document(
        metadata=_ticket_metadata(ticket),
        sections=[
            {
                "department_id": s.department_id,
                "approver": s.approver,
                "draft_content": s.draft_content,
            }
            for s in sections
        ],
    )
    generated_at = assembled["generated_at"]
    if not isinstance(generated_at, datetime):
        generated_at = datetime.now(timezone.utc)

    rfp_repository.upsert_final_document(
        session,
        ticket_id=ticket_id,
        content=assembled["content"],
        currency=assembled["currency"],
        sections=list(assembled["sections"]),
        generated_at=generated_at,
    )
    ticket = rfp_repository.get_ticket(session, ticket_id) or ticket
    rfp_repository.append_ticket_trace(
        session,
        ticket,
        [
            make_trace_entry(
                agent="assemble_final_document",
                input_payload={"sections": [s.department_id for s in sections]},
                output_payload={"currency": assembled["currency"], "status": "terminado"},
                part=3,
            )
        ],
    )
    ticket = rfp_repository.get_ticket(session, ticket_id) or ticket
    return rfp_repository.update_ticket_fields(
        session,
        ticket,
        status="terminado",
        approval_phase=None,
        final_document_content=assembled["content"],
        final_document_currency=assembled["currency"],
        final_document_generated_at=generated_at,
    )


def decide_section(
    session: Session,
    ticket_id: str,
    department_id: str,
    *,
    action: str,
    comment: str | None = None,
) -> SectionDecisionResponse:
    """Resume a department interrupt with approve/reject without blocking sibling departments."""
    from datetime import datetime, timezone

    from ..rfp.part3 import resume_department_approval

    ticket = rfp_repository.get_ticket(session, ticket_id)
    if ticket is None:
        raise ValueError("Ticket not found")
    if ticket.approval_phase != "section_signoff":
        raise ValueError("Ticket is not in section sign-off phase")
    section = rfp_repository.get_section(session, ticket_id=ticket_id, department_id=department_id)
    if section is None:
        raise ValueError("Section not found")

    result = resume_department_approval(
        ticket_id=ticket_id,
        department_id=department_id,
        action=action,
        comment=comment,
    )
    values = result.get("values") or {}
    status = str(result.get("approval_status") or values.get("approval_status") or section.approval_status)
    fields: dict[str, Any] = {
        "approval_status": status,
        "human_approval_rounds": int(
            result.get("human_approval_rounds")
            or values.get("human_approval_rounds")
            or section.human_approval_rounds
            or 0
        ),
    }
    if result.get("draft_content") or values.get("draft_content"):
        fields["draft_content"] = result.get("draft_content") or values.get("draft_content")
    if status == "approved":
        fields["approved_at"] = datetime.now(timezone.utc)
    rfp_repository.update_section_fields(session, section, **fields)

    logs = list(result.get("node_logs") or values.get("node_logs") or [])
    if logs:
        ticket = rfp_repository.get_ticket(session, ticket_id) or ticket
        rfp_repository.append_ticket_trace(session, ticket, logs)

    if status == "rejected" and (result.get("arbitration_action") == "discard_ticket"):
        ticket = rfp_repository.get_ticket(session, ticket_id) or ticket
        rfp_repository.update_ticket_fields(
            session, ticket, status="descartado", approval_phase=None
        )
    elif status == "approved":
        _maybe_assemble_final(session, ticket_id)

    ticket = rfp_repository.get_ticket(session, ticket_id) or ticket
    interrupted = bool(result.get("interrupted"))
    return SectionDecisionResponse(
        ticket_id=ticket_id,
        department_id=department_id,
        approval_status=status,
        status=ticket.status,
        interrupted=interrupted,
        message=(
            f"Decisión '{action}' aplicada a {department_id}. "
            + ("Esperando siguiente interrupt." if interrupted else f"Estado sección: {status}.")
        ),
    )


def arbitrate_section(
    session: Session,
    ticket_id: str,
    department_id: str,
    *,
    action: str,
    comment: str | None = None,
) -> SectionDecisionResponse:
    """Resume the explicit arbitration node for a department branch."""
    return decide_section(
        session,
        ticket_id,
        department_id,
        action=action,
        comment=comment,
    )


def approve_intake(session: Session, ticket_id: str) -> ApproveIntakeResponse:
    ticket = rfp_repository.get_ticket(session, ticket_id)
    if ticket is None:
        raise ValueError("Ticket not found")
    if ticket.status != "esperando_aprobación" or ticket.approval_phase != "intake":
        raise ValueError("Ticket is not waiting for intake approval")

    rfp_repository.update_ticket_fields(
        session,
        ticket,
        status="generando_borrador",
        approval_phase=None,
    )

    task_id: str | None = None
    try:
        from ..tasks.rfp import run_rfp_part2_task

        async_result = run_rfp_part2_task.delay({"ticket_id": ticket_id})
        task_id = async_result.id
        ticket = rfp_repository.update_ticket_fields(session, ticket, celery_task_id=task_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Celery Parte 2 enqueue failed for %s; running inline: %s", ticket_id, exc)
        ticket = process_rfp_part2(session, ticket_id)

    session.refresh(ticket)
    return ApproveIntakeResponse(
        ticket_id=ticket_id,
        status=ticket.status,
        message=(
            "Intake aprobado. Generación, evaluación y pausa HITL (Parte 2–3) en curso "
            f"(task={task_id or 'inline'})."
        ),
    )


def list_ticket_summaries(session: Session) -> list[RfpTicketSummary]:
    return [ticket_to_summary(t) for t in rfp_repository.list_tickets(session)]
