"""Persistence helpers for RFP tickets and department sections."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session, select

from ..models import RfpDepartmentSection, RfpTicket


def create_ticket(
    session: Session,
    *,
    ticket_id: str,
    rfp_id: str,
    original_filename: str,
    pdf_path: str,
    created_by_user_uuid: str | None,
) -> RfpTicket:
    now = datetime.now(timezone.utc)
    ticket = RfpTicket(
        ticket_id=ticket_id,
        rfp_id=rfp_id,
        status="analizando",
        original_filename=original_filename,
        pdf_path=pdf_path,
        created_by_user_uuid=created_by_user_uuid,
        created_at=now,
        updated_at=now,
    )
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket


def get_ticket(session: Session, ticket_id: str) -> RfpTicket | None:
    return session.get(RfpTicket, ticket_id)


def list_tickets(session: Session, *, limit: int = 50) -> list[RfpTicket]:
    statement = select(RfpTicket).order_by(RfpTicket.created_at.desc()).limit(limit)
    return list(session.exec(statement).all())


def list_sections(session: Session, ticket_id: str) -> list[RfpDepartmentSection]:
    statement = select(RfpDepartmentSection).where(RfpDepartmentSection.ticket_id == ticket_id)
    return list(session.exec(statement).all())


def update_ticket_fields(session: Session, ticket: RfpTicket, **fields: Any) -> RfpTicket:
    for key, value in fields.items():
        setattr(ticket, key, value)
    ticket.updated_at = datetime.now(timezone.utc)
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket


def replace_sections(
    session: Session,
    *,
    ticket_id: str,
    sections: list[dict[str, Any]],
) -> list[RfpDepartmentSection]:
    existing = list_sections(session, ticket_id)
    for row in existing:
        session.delete(row)
    session.commit()

    created: list[RfpDepartmentSection] = []
    now = datetime.now(timezone.utc)
    for item in sections:
        row = RfpDepartmentSection(
            ticket_id=ticket_id,
            department_id=item["department_id"],
            key_aspects=list(item.get("key_aspects") or []),
            approver=item["approver"],
            approval_status="pending",
            created_at=now,
            updated_at=now,
        )
        session.add(row)
        created.append(row)
    session.commit()
    for row in created:
        session.refresh(row)
    return created
