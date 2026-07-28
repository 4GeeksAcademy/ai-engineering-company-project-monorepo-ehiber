"""Persistence for CX agent episodic memory (propose → decide → consolidate)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlmodel import Session, col, select

from ..models import AgentMemoryAudit, AgentMemoryEntry, AgentMemoryProposal

MAX_TOTAL_ENTRIES = 100
TTL_DAYS = 90


def create_proposal(session: Session, proposal: AgentMemoryProposal) -> AgentMemoryProposal:
    session.add(proposal)
    session.commit()
    session.refresh(proposal)
    return proposal


def get_proposal(session: Session, proposal_id: str) -> AgentMemoryProposal | None:
    return session.get(AgentMemoryProposal, proposal_id)


def get_pending_proposal_for_user(
    session: Session, *, user_uuid: str
) -> AgentMemoryProposal | None:
    statement = (
        select(AgentMemoryProposal)
        .where(
            AgentMemoryProposal.user_uuid == user_uuid,
            AgentMemoryProposal.status == "pending",
        )
        .order_by(col(AgentMemoryProposal.created_at).desc())
    )
    return session.exec(statement).first()


def mark_proposal_status(
    session: Session,
    proposal: AgentMemoryProposal,
    *,
    status: str,
) -> AgentMemoryProposal:
    proposal.status = status
    proposal.resolved_at = datetime.now(timezone.utc)
    session.add(proposal)
    session.commit()
    session.refresh(proposal)
    return proposal


def append_audit(session: Session, audit: AgentMemoryAudit) -> AgentMemoryAudit:
    session.add(audit)
    session.commit()
    session.refresh(audit)
    return audit


def list_audits_for_user(
    session: Session, *, user_uuid: str, limit: int = 50
) -> list[AgentMemoryAudit]:
    statement = (
        select(AgentMemoryAudit)
        .where(AgentMemoryAudit.user_uuid == user_uuid)
        .order_by(col(AgentMemoryAudit.created_at).desc())
        .limit(limit)
    )
    return list(session.exec(statement).all())


def upsert_approved_entry(session: Session, entry: AgentMemoryEntry) -> AgentMemoryEntry:
    existing = session.exec(
        select(AgentMemoryEntry).where(
            AgentMemoryEntry.user_uuid == entry.user_uuid,
            AgentMemoryEntry.consolidation_key == entry.consolidation_key,
        )
    ).first()
    now = datetime.now(timezone.utc)
    if existing is None:
        session.add(entry)
        session.commit()
        session.refresh(entry)
        _enforce_limits(session, user_uuid=entry.user_uuid)
        return entry

    existing.content = entry.content
    existing.carrier = entry.carrier
    existing.country = entry.country
    existing.topic = entry.topic
    existing.authorized_by = entry.authorized_by
    existing.proposal_id = entry.proposal_id
    existing.updated_at = now
    existing.expires_at = entry.expires_at
    session.add(existing)
    session.commit()
    session.refresh(existing)
    return existing


def list_active_entries(
    session: Session, *, user_uuid: str, limit: int = 20
) -> list[AgentMemoryEntry]:
    now = datetime.now(timezone.utc)
    statement = (
        select(AgentMemoryEntry)
        .where(
            AgentMemoryEntry.user_uuid == user_uuid,
            AgentMemoryEntry.expires_at > now,
        )
        .order_by(col(AgentMemoryEntry.updated_at).desc())
        .limit(limit)
    )
    return list(session.exec(statement).all())


def default_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=TTL_DAYS)


def _enforce_limits(session: Session, *, user_uuid: str) -> None:
    now = datetime.now(timezone.utc)
    # Drop expired first.
    expired = list(
        session.exec(
            select(AgentMemoryEntry).where(
                AgentMemoryEntry.user_uuid == user_uuid,
                AgentMemoryEntry.expires_at <= now,
            )
        ).all()
    )
    for row in expired:
        session.delete(row)
    session.commit()

    rows = list(
        session.exec(
            select(AgentMemoryEntry)
            .where(AgentMemoryEntry.user_uuid == user_uuid)
            .order_by(col(AgentMemoryEntry.updated_at).asc())
        ).all()
    )
    overflow = len(rows) - MAX_TOTAL_ENTRIES
    if overflow <= 0:
        return
    for row in rows[:overflow]:
        session.delete(row)
    session.commit()
