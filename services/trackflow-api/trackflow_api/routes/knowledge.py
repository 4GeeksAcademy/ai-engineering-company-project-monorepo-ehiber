from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.config import get_settings
from ..core.rate_limit import knowledge_ask_limiter
from ..core.security import get_current_user
from ..schemas.knowledge import (
    AskRequest,
    AskResponse,
    GuardrailStatsResponse,
    MemoryAuditItem,
    MemoryAuditListResponse,
)
from ..schemas.users import UserPublic
from ..services.rag_service import ask, get_run_trace, guardrail_stats, memory_audits

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.post("/ask", response_model=AskResponse)
def ask_knowledge(
    payload: AskRequest,
    current_user: Annotated[UserPublic, Depends(get_current_user)],
) -> AskResponse:
    settings = get_settings()
    if not knowledge_ask_limiter.allow(
        current_user.user_uuid,
        settings.knowledge_ask_rate_limit,
        settings.knowledge_ask_rate_window_seconds,
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many knowledge requests. Wait before asking again.",
        )
    try:
        return ask(
            payload.question,
            user_uuid=current_user.user_uuid,
            memory_decision=payload.memory_decision,
            proposal_id=payload.proposal_id,
            edited_content=payload.edited_content,
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=503,
            detail="No se pudo completar la consulta de conocimiento. Inténtalo de nuevo más tarde.",
        ) from exc


@router.get("/runs/{run_id}")
def knowledge_run_trace(
    run_id: str,
    current_user: Annotated[UserPublic, Depends(get_current_user)],
) -> dict:
    _ = current_user
    return get_run_trace(run_id)


@router.get("/guardrails/stats", response_model=GuardrailStatsResponse)
def knowledge_guardrail_stats(
    current_user: Annotated[UserPublic, Depends(get_current_user)],
) -> GuardrailStatsResponse:
    _ = current_user
    stats = guardrail_stats()
    return GuardrailStatsResponse(
        by_failure_type=stats.get("by_failure_type") or {},
        by_guardrail=stats.get("by_guardrail") or {},
        total=int(stats.get("total") or 0),
    )


@router.get("/memory/audits", response_model=MemoryAuditListResponse)
def knowledge_memory_audits(
    current_user: Annotated[UserPublic, Depends(get_current_user)],
) -> MemoryAuditListResponse:
    items = memory_audits(user_uuid=current_user.user_uuid)
    return MemoryAuditListResponse(items=[MemoryAuditItem(**item) for item in items])
