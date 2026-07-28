from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException

from ..agent.graph import get_compiled_knowledge_graph
from ..agent.guardrails import get_guardrail_stats
from ..agent.tracing import get_trace, store_trace
from ..schemas.knowledge import AskResponse, SourceReferenceResponse, TraceStepResponse


def _safe_user_error(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=503,
        detail="No se pudo completar la consulta de conocimiento. Inténtalo de nuevo más tarde.",
    )


def ask(question: str, *, user_uuid: str | None = None) -> AskResponse:
    run_id = str(uuid.uuid4())
    graph = get_compiled_knowledge_graph()
    config = {"configurable": {"thread_id": run_id}}

    try:
        final_state = graph.invoke(
            {
                "run_id": run_id,
                "raw_question": question,
                "user_uuid": user_uuid,
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
    }
    store_trace(run_id, payload)

    return AskResponse(
        answer=answer,
        sources=sources,
        run_id=run_id,
        trace=trace_steps,
        checkpointed=checkpointed,
    )


def get_run_trace(run_id: str) -> dict[str, Any]:
    payload = get_trace(run_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Run trace not found.")
    return payload


def guardrail_stats() -> dict[str, Any]:
    return get_guardrail_stats()
