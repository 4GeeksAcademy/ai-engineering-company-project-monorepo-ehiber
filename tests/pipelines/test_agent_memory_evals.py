"""Consent-based memory evals for TrackFlow CX agent (MEM-092 / Milestone 8 memory)."""

from __future__ import annotations

import pytest

from trackflow_api.agent.graph import reset_compiled_knowledge_graph
from trackflow_api.agent.guardrails import reset_guardrail_stats
from trackflow_api.agent.memory import (
    classify_memory_decision,
    contains_forbidden_memory_content,
    evaluate_memory_candidate,
    list_user_audits,
    load_approved_memories,
)
from trackflow_api.agent.tracing import clear_traces
from trackflow_api.rag.types import QueryResult, RetrievedChunk, SourceReference
from trackflow_api.services.rag_service import ask

TEST_USER = "memory-user-aaaa"


@pytest.fixture(autouse=True)
def _reset_agent_runtime():
    reset_compiled_knowledge_graph()
    clear_traces()
    reset_guardrail_stats()
    yield
    reset_compiled_knowledge_graph()
    clear_traces()
    reset_guardrail_stats()


def _patch_rag(monkeypatch, *, answer: str = "Anotado."):
    chunks = [
        RetrievedChunk(
            id="c1",
            text="Cobertura de transportistas TrackFlow.",
            score=0.9,
            source_document="carrier-coverage",
            section="Cobertura",
        )
    ]

    def fake_retrieve(_question: str, *, top_k: int | None = None):
        return chunks

    def fake_query(_question: str, retrieved, *, policy_country_lock=None, approved_memories=None):
        return QueryResult(
            answer=answer,
            sources=[
                SourceReference(source_document="carrier-coverage", section="Cobertura")
            ]
            if retrieved
            else [],
        )

    monkeypatch.setattr("trackflow_api.agent.nodes.rag_pipeline.retrieve", fake_retrieve)
    monkeypatch.setattr("trackflow_api.agent.nodes.rag_pipeline.query", fake_query)


def test_eval_should_propose_carrier_correction(monkeypatch):
    _patch_rag(monkeypatch, answer="Gracias por la corrección operativa.")
    question = (
        "En realidad SEUR ya no cubre esa zona rural de Zaragoza, "
        "hay que usar el carrier local desde el mes pasado."
    )
    result = ask(question, user_uuid=TEST_USER)
    assert result.memory_proposal is not None
    assert "propose_memory" in [s.node for s in result.trace]
    assert result.memory_proposal.country == "ES" or "SEUR" in result.memory_proposal.content.upper()
    assert "recuerde" in result.answer.lower() or "recordar" in result.answer.lower()


def test_eval_should_not_propose_one_off_tracking(monkeypatch):
    _patch_rag(monkeypatch)
    result = ask("¿Dónde está el paquete con tracking XJ4471?", user_uuid=TEST_USER)
    assert result.memory_proposal is None


def test_eval_approve_consolidates_and_audits(monkeypatch):
    _patch_rag(monkeypatch, answer="Queda registrado el contexto operativo.")
    first = ask(
        "El cliente de cosméticos siempre quiere su reporte mensual con el desglose "
        "de devoluciones primero, antes que el volumen de envíos.",
        user_uuid=TEST_USER,
    )
    assert first.memory_proposal is not None
    proposal_id = first.memory_proposal.proposal_id

    second = ask(
        "Sí, guarda esa memoria.",
        user_uuid=TEST_USER,
        memory_decision="approve",
        proposal_id=proposal_id,
    )
    assert second.memory_decision is not None
    assert second.memory_decision.handled is True
    assert second.memory_decision.decision == "approved"

    memories = load_approved_memories(user_uuid=TEST_USER)
    assert len(memories) >= 1
    audits = list_user_audits(user_uuid=TEST_USER)
    events = {item["event_type"] for item in audits}
    assert "proposed" in events
    assert "approved" in events


def test_eval_reject_keeps_audit_without_entry(monkeypatch):
    user = "memory-user-reject"
    _patch_rag(monkeypatch)
    first = ask(
        "El cliente de cosméticos siempre quiere su reporte mensual con el desglose "
        "de devoluciones primero, antes que el volumen de envíos.",
        user_uuid=user,
    )
    assert first.memory_proposal is not None
    second = ask(
        "No, no lo guardes.",
        user_uuid=user,
        memory_decision="reject",
        proposal_id=first.memory_proposal.proposal_id,
    )
    assert second.memory_decision.decision == "rejected"
    assert load_approved_memories(user_uuid=user) == []
    events = {item["event_type"] for item in list_user_audits(user_uuid=user)}
    assert "rejected" in events
    assert "proposed" in events


def test_eval_unclear_never_approves():
    result = classify_memory_decision(message="tal vez luego vemos")
    assert result.decision == "unclear"


def test_eval_forbidden_sensitive_content():
    assert contains_forbidden_memory_content(
        "La dirección exacta del cliente es Calle Mayor 12 y la ruta interna del almacén."
    )
    candidate = evaluate_memory_candidate(
        question="Guarda la dirección exacta del cliente en Calle Mayor 12",
        answer="Ok",
    )
    assert candidate is None


def test_eval_self_eval_checklist_positive_cases():
    should = [
        "En realidad SEUR ya no cubre esa zona rural de Zaragoza, hay que usar el carrier local desde el mes pasado.",
        "Esos retrasos reportados en incidencias de Los Ángeles esta semana son por la huelga portuaria, no por un problema nuestro — ya van tres tickets sobre lo mismo.",
        "El cliente de cosméticos siempre quiere su reporte mensual con el desglose de devoluciones primero, antes que el volumen de envíos.",
    ]
    for text in should:
        candidate = evaluate_memory_candidate(question=text, answer="Anotado.")
        assert candidate is not None, text
        assert candidate.should_propose is True


def test_eval_self_eval_checklist_negative_cases():
    should_not = [
        "¿Dónde está el paquete con tracking XJ4471?",
        "Perfecto, ya quedó resuelto.",
        "Tradúceme esto al inglés para el cliente.",
    ]
    for text in should_not:
        candidate = evaluate_memory_candidate(question=text, answer="Ok.")
        assert candidate is None, text
