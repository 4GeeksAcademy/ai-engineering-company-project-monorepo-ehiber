from __future__ import annotations

import time
from typing import Any

from . import path_setup  # noqa: F401 — ensure monorepo root is importable
from data.pipelines import rag as rag_pipeline

from .state import AgentState
from .tracing import timed_step

MIN_QUESTION_LENGTH = 3


def _chunk_to_dict(chunk: rag_pipeline.RetrievedChunk) -> dict[str, Any]:
    return {
        "id": chunk.id,
        "text": chunk.text,
        "score": chunk.score,
        "source_document": chunk.source_document,
        "section": chunk.section,
    }


def _dicts_to_chunks(chunk_dicts: list[dict]) -> list[rag_pipeline.RetrievedChunk]:
    return [
        rag_pipeline.RetrievedChunk(
            id=item["id"],
            text=item["text"],
            score=float(item["score"]),
            source_document=item["source_document"],
            section=item["section"],
        )
        for item in chunk_dicts
    ]


def receive_question(state: AgentState) -> dict[str, Any]:
    """Validate and normalize the incoming question."""
    started = time.perf_counter()
    raw = (state.get("raw_question") or state.get("question") or "").strip()
    elapsed_ms = int((time.perf_counter() - started) * 1000)

    if len(raw) < MIN_QUESTION_LENGTH:
        step = timed_step(
            "receive_question",
            {"reason": "question_too_short", "length": len(raw)},
            status="error",
        )
        step["ms"] = elapsed_ms
        return {
            "question": raw,
            "error": "La pregunta es demasiado corta para consultar la base de conocimiento.",
            "node_trace": [step],
        }

    step = timed_step("receive_question", {"length": len(raw)})
    step["ms"] = elapsed_ms
    return {
        "question": raw,
        "error": None,
        "node_trace": [step],
    }


def retrieve_context(state: AgentState) -> dict[str, Any]:
    """Retrieve knowledge chunks via data.pipelines.rag.retrieve (Milestone 7)."""
    started = time.perf_counter()
    question = state["question"]
    chunks = rag_pipeline.retrieve(question)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    serialized = [_chunk_to_dict(chunk) for chunk in chunks]
    top_score = max((chunk["score"] for chunk in serialized), default=0.0)
    step = timed_step(
        "retrieve",
        {
            "chunk_count": len(serialized),
            "top_score": top_score,
            "sources": [chunk["source_document"] for chunk in serialized],
        },
    )
    step["ms"] = elapsed_ms
    return {"chunks": serialized, "node_trace": [step]}


def generate_answer(state: AgentState) -> dict[str, Any]:
    """Generate the final answer when retrieval returned context."""
    started = time.perf_counter()
    chunks = _dicts_to_chunks(state.get("chunks") or [])
    result = rag_pipeline.query(state["question"], chunks)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    sources = [
        {"source_document": source.source_document, "section": source.section}
        for source in result.sources
    ]
    step = timed_step(
        "generate_answer",
        {"source_count": len(sources), "path": "with_context"},
    )
    step["ms"] = elapsed_ms
    return {
        "answer": result.answer,
        "sources": sources,
        "error": None,
        "node_trace": [step],
    }


def generate_no_context(state: AgentState) -> dict[str, Any]:
    """Generate when retrieval found no chunks — still uses Milestone 7 query."""
    started = time.perf_counter()
    result = rag_pipeline.query(state["question"], [])
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    step = timed_step(
        "generate_no_context",
        {"source_count": 0, "path": "empty_retrieval"},
    )
    step["ms"] = elapsed_ms
    return {
        "answer": result.answer,
        "sources": [],
        "error": None,
        "node_trace": [step],
    }


def abort_invalid(state: AgentState) -> dict[str, Any]:
    """Terminal path when receive_question rejects the input (no LLM call)."""
    message = state.get("error") or (
        "No se pudo procesar la pregunta. Reformúlala e inténtalo de nuevo."
    )
    step = timed_step("abort_invalid", {"handled": True}, status="error")
    return {
        "answer": message,
        "sources": [],
        "node_trace": [step],
    }


def route_after_receive(state: AgentState) -> str:
    """Route by receive_question output: error → abort, else → retrieve."""
    if state.get("error"):
        return "abort_invalid"
    return "retrieve"


def route_after_retrieve(state: AgentState) -> str:
    """Route by retrieval output: empty chunks → no-context path, else generate."""
    chunks = state.get("chunks") or []
    if not chunks:
        return "generate_no_context"
    return "generate_answer"
