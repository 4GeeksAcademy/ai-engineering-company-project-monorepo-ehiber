from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException

from ..agent.graph import get_compiled_knowledge_graph
from ..agent.guardrails import get_guardrail_stats
from ..agent.memory import list_user_audits
from ..agent.tracing import get_trace, store_trace
from ..schemas.knowledge import (
    AskResponse,
    MemoryDecisionResponse,
    MemoryProposalResponse,
    SourceReferenceResponse,
    TraceStepResponse,
)


def _safe_user_error(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=503,
        detail="No se pudo completar la consulta de conocimiento. Inténtalo de nuevo más tarde.",
    )


def ask(
    question: str,
    *,
    user_uuid: str | None = None,
    memory_decision: str | None = None,
    proposal_id: str | None = None,
    edited_content: str | None = None,
) -> AskResponse:
    run_id = str(uuid.uuid4())
    graph = get_compiled_knowledge_graph()
    config = {"configurable": {"thread_id": run_id}}

    try:
        final_state = graph.invoke(
            {
                "run_id": run_id,
                "raw_question": question,
                "user_uuid": user_uuid,
                "memory_decision": memory_decision,
                "memory_proposal_id": proposal_id,
                "memory_edited_content": edited_content,
                "node_trace": [],
            },
            config=config,
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001 — map internals to safe client error
        raise _safe_user_error(exc) from exc

    answer = str(final_state.get("answer") or "")
    sources = [
        SourceReferenceResponse(
            source_document=source["source_document"],
            section=source["section"],
        )
        for source in (final_state.get("sources") or [])
    ]
    trace_steps = [
        TraceStepResponse(
            node=str(step.get("node", "")),
            status=str(step.get("status", "ok")),
            ms=int(step.get("ms", 0)),
            detail=dict(step.get("detail") or {}),
        )
        for step in (final_state.get("node_trace") or [])
    ]

    # Verifiable checkpoint for this run/thread
    checkpoint_state = graph.get_state(config)
    checkpointed = checkpoint_state is not None and checkpoint_state.values is not None

    proposal_raw = final_state.get("memory_proposal")
    proposal = None
    if isinstance(proposal_raw, dict) and proposal_raw.get("proposal_id"):
        proposal = MemoryProposalResponse(
            proposal_id=str(proposal_raw["proposal_id"]),
            content=str(proposal_raw.get("content") or ""),
            consolidation_key=str(proposal_raw.get("consolidation_key") or ""),
            carrier=proposal_raw.get("carrier"),
            country=proposal_raw.get("country"),
            topic=proposal_raw.get("topic"),
            status=str(proposal_raw.get("status") or "pending"),
        )

    decision_raw = final_state.get("memory_decision_result") or {}
    decision = MemoryDecisionResponse(
        handled=bool(decision_raw.get("handled")),
        decision=decision_raw.get("decision"),
        proposal_id=decision_raw.get("proposal_id"),
        message=decision_raw.get("message"),
    )

    # If the user only resolved memory and the main answer is empty, surface decision message.
    if decision.handled and decision.message and not answer.strip():
        answer = str(decision.message)

    payload: dict[str, Any] = {
        "run_id": run_id,
        "question": final_state.get("question") or question,
        "user_uuid": user_uuid,
        "answer": answer,
        "sources": [source.model_dump() for source in sources],
        "trace": [step.model_dump() for step in trace_steps],
        "checkpointed": checkpointed,
        "error": final_state.get("error"),
        "guardrail_stats": get_guardrail_stats(),
        "memory_proposal": proposal.model_dump() if proposal else None,
        "memory_decision": decision.model_dump(),
    }
    store_trace(run_id, payload)

    return AskResponse(
        answer=answer,
        sources=sources,
        run_id=run_id,
        trace=trace_steps,
        checkpointed=checkpointed,
        memory_proposal=proposal,
        memory_decision=decision,
    )


def get_run_trace(run_id: str) -> dict[str, Any]:
    payload = get_trace(run_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Run trace not found.")
    return payload


def guardrail_stats() -> dict[str, Any]:
    return get_guardrail_stats()


def memory_audits(*, user_uuid: str, limit: int = 50) -> list[dict[str, Any]]:
    return list_user_audits(user_uuid=user_uuid, limit=limit)
