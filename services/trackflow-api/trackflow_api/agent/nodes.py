from __future__ import annotations

import json
import re
import time
from typing import Any

from . import path_setup  # noqa: F401 — ensure monorepo root is importable
from data.pipelines import rag as rag_pipeline

from .state import AgentState
from .tools import lookup_incident_tool, lookup_inventory_tool, parse_tool_result
from .tracing import timed_step
from ..rag.litellm_client import create_completion

MIN_QUESTION_LENGTH = 3

TOOL_SYSTEM_PROMPT = """Eres un account manager de TrackFlow respondiendo con datos operativos en tiempo real.

Usa ÚNICAMENTE el resultado de la herramienta (tool_result) para responder.
Si tool_result indica error o no encontrado, dilo con claridad y no inventes estados, tickets ni stock.
Responde en español, tono profesional y breve."""


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


def classify_intent(question: str) -> str:
    """Decide autonomously: incident | inventory | rag."""
    text = question.lower()

    inventory_hints = (
        "stock",
        "inventario",
        "sku",
        "almacén",
        "almacen",
        "tenemos de",
        "hay unidades",
        "existencia",
    )
    if any(hint in text for hint in inventory_hints) or re.search(
        r"\b[a-z]{2,}[-_][a-z0-9][-_a-z0-9]*\b", text, flags=re.IGNORECASE
    ):
        if re.search(r"\b(sku|stock|inventario|almac[eé]n|unidades)\b", text, flags=re.IGNORECASE):
            return "inventory"

    incident_hints = (
        "ticket",
        "incidencia",
        "incident",
        "estado del",
        "estado de la",
        "estado de",
        "reclamación",
        "reclamacion",
    )
    if any(hint in text for hint in incident_hints) or re.search(
        r"\b(ticket|incidencia|incident)\s*[#:.-]?\s*\w+", text, flags=re.IGNORECASE
    ):
        return "incident"

    if re.search(r"\b(estado|status|seguimiento)\b", text) and re.search(r"\b\d{1,8}\b", text):
        return "incident"

    return "rag"


def receive_question(state: AgentState) -> dict[str, Any]:
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


def classify_question(state: AgentState) -> dict[str, Any]:
    started = time.perf_counter()
    intent = classify_intent(state["question"])
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    step = timed_step("classify_intent", {"intent": intent})
    step["ms"] = elapsed_ms
    return {"intent": intent, "node_trace": [step]}


def retrieve_context(state: AgentState) -> dict[str, Any]:
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


def tool_incidents(state: AgentState) -> dict[str, Any]:
    started = time.perf_counter()
    result = parse_tool_result(lookup_incident_tool(state["question"])).model_dump()
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    ok = bool(result.get("ok"))
    step = timed_step(
        "tool_incidents",
        {
            "ok": ok,
            "error": result.get("error"),
            "found": (result.get("data") or {}).get("found") if ok else False,
            "via": "mcp",
        },
        status="ok" if ok else "error",
    )
    step["ms"] = elapsed_ms
    return {
        "tool_name": "get_incident",
        "tool_result": result,
        "tool_error": None if ok else str(result.get("error") or "tool_failed"),
        "node_trace": [step],
    }


def tool_inventory(state: AgentState) -> dict[str, Any]:
    started = time.perf_counter()
    result = parse_tool_result(lookup_inventory_tool(state["question"])).model_dump()
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    ok = bool(result.get("ok"))
    step = timed_step(
        "tool_inventory",
        {
            "ok": ok,
            "error": result.get("error"),
            "found": (result.get("data") or {}).get("found") if ok else False,
            "via": "mcp",
        },
        status="ok" if ok else "error",
    )
    step["ms"] = elapsed_ms
    return {
        "tool_name": "query_inventory",
        "tool_result": result,
        "tool_error": None if ok else str(result.get("error") or "tool_failed"),
        "node_trace": [step],
    }


def tool_recovery(state: AgentState) -> dict[str, Any]:
    tool_result = state.get("tool_result") or {}
    message = tool_result.get("message") or (
        "No pude consultar el sistema operativo en este momento. "
        "Por favor reintenta o escala al equipo interno."
    )
    step = timed_step(
        "tool_recovery",
        {
            "tool_name": state.get("tool_name"),
            "error": state.get("tool_error") or tool_result.get("error"),
            "recovered": True,
        },
        status="error",
    )
    recovered = {
        "ok": False,
        "error": state.get("tool_error") or tool_result.get("error") or "tool_failed",
        "message": message,
        "data": tool_result.get("data"),
    }
    return {
        "tool_result": recovered,
        "tool_error": recovered["error"],
        "node_trace": [step],
    }


def generate_answer(state: AgentState) -> dict[str, Any]:
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


def generate_from_tool(state: AgentState) -> dict[str, Any]:
    started = time.perf_counter()
    tool_result = state.get("tool_result") or {}
    user_prompt = (
        f"Pregunta del usuario:\n{state['question']}\n\n"
        f"Resultado de la herramienta ({state.get('tool_name') or 'tool'}):\n"
        f"{json.dumps(tool_result, ensure_ascii=False)}"
    )
    answer = create_completion(system_prompt=TOOL_SYSTEM_PROMPT, user_prompt=user_prompt)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    source_label = "incident-mcp" if state.get("intent") == "incident" else "inventory-mcp"
    step = timed_step(
        "generate_from_tool",
        {
            "tool_name": state.get("tool_name"),
            "tool_ok": bool(tool_result.get("ok")),
            "path": "mcp_tool",
        },
    )
    step["ms"] = elapsed_ms
    return {
        "answer": answer,
        "sources": [{"source_document": source_label, "section": "live-query"}],
        "error": None,
        "node_trace": [step],
    }


def abort_invalid(state: AgentState) -> dict[str, Any]:
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
    if state.get("error"):
        return "abort_invalid"
    return "classify_intent"


def route_after_classify(state: AgentState) -> str:
    intent = state.get("intent") or "rag"
    if intent == "incident":
        return "tool_incidents"
    if intent == "inventory":
        return "tool_inventory"
    return "retrieve"


def route_after_retrieve(state: AgentState) -> str:
    chunks = state.get("chunks") or []
    if not chunks:
        return "generate_no_context"
    return "generate_answer"


def route_after_tool(state: AgentState) -> str:
    tool_result = state.get("tool_result") or {}
    if tool_result.get("ok"):
        return "generate_from_tool"
    return "tool_recovery"
