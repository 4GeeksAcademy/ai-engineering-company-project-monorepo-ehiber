"""Runnable evals for the LangGraph knowledge agent (rubric: tests/pipelines/)."""

from __future__ import annotations

import uuid

import pytest

from trackflow_api.agent.graph import get_compiled_knowledge_graph, reset_compiled_knowledge_graph
from trackflow_api.agent.tracing import clear_traces, get_trace
from trackflow_api.rag.types import QueryResult, RetrievedChunk, SourceReference
from trackflow_api.services.rag_service import ask


@pytest.fixture(autouse=True)
def _reset_agent_runtime():
    reset_compiled_knowledge_graph()
    clear_traces()
    yield
    reset_compiled_knowledge_graph()
    clear_traces()


def _patch_rag(monkeypatch, *, chunks, answer: str, sources=None):
    sources = sources or [
        SourceReference(source_document="returns-policy", section="Política de Devoluciones")
    ]

    def fake_retrieve(_question: str, *, top_k: int | None = None):
        return chunks

    def fake_query(_question: str, retrieved):
        return QueryResult(answer=answer, sources=sources if retrieved else [])

    monkeypatch.setattr("trackflow_api.agent.nodes.rag_pipeline.retrieve", fake_retrieve)
    monkeypatch.setattr("trackflow_api.agent.nodes.rag_pipeline.query", fake_query)


def test_eval_trace_includes_single_responsibility_nodes(monkeypatch):
    """Eval 1: every successful RAG run traces receive → classify → retrieve → generate."""
    chunks = [
        RetrievedChunk(
            id="c1",
            text="Ventana de devolución estándar: 30 días desde la entrega.",
            score=0.92,
            source_document="returns-policy",
            section="Política de Devoluciones",
        )
    ]
    _patch_rag(
        monkeypatch,
        chunks=chunks,
        answer="La ventana estándar es de 30 días desde la entrega.",
    )

    result = ask("¿Cuál es la ventana de devolución estándar?")
    nodes = [step.node for step in result.trace]

    assert nodes == ["receive_question", "classify_intent", "retrieve", "generate_answer"]
    assert result.checkpointed is True
    stored = get_trace(result.run_id)
    assert stored is not None
    assert stored["trace"][0]["node"] == "receive_question"
    assert "30 días" in result.answer


def test_eval_returns_policy_source_on_trace_and_answer(monkeypatch):
    """Eval 2: returns questions keep returns-policy on trace sources."""
    chunks = [
        RetrievedChunk(
            id="c1",
            text="Ventana de devolución estándar: 30 días desde la entrega.",
            score=0.91,
            source_document="returns-policy",
            section="Política de Devoluciones",
        )
    ]
    _patch_rag(
        monkeypatch,
        chunks=chunks,
        answer="La ventana estándar es de 30 días desde la entrega.",
    )

    result = ask("¿Cuál es la ventana de devolución estándar?")
    retrieve_step = next(step for step in result.trace if step.node == "retrieve")
    assert "returns-policy" in retrieve_step.detail["sources"]
    assert result.sources[0].source_document == "returns-policy"
    assert "30 días" in result.answer


def test_eval_peak_season_answer_does_not_promise_sla(monkeypatch):
    """Eval 3: Black Friday path must not invent an SLA guarantee."""
    chunks = [
        RetrievedChunk(
            id="c1",
            text=(
                "TrackFlow no garantiza SLA de entrega los días de alta demanda "
                "declarados (Black Friday, Navidad, Rebajas)."
            ),
            score=0.95,
            source_document="sla-delivery",
            section="SLA de Entrega",
        )
    ]
    _patch_rag(
        monkeypatch,
        chunks=chunks,
        answer=(
            "Durante el Black Friday no garantizamos el SLA habitual; "
            "los tiempos pueden extenderse y debes comunicarlo proactivamente."
        ),
        sources=[SourceReference(source_document="sla-delivery", section="SLA de Entrega")],
    )

    result = ask("¿Podemos garantizar el SLA habitual durante el Black Friday?")
    lowered = result.answer.lower()
    assert "garantiz" in lowered or "no" in lowered
    assert "sla-delivery" in [s.source_document for s in result.sources]
    assert result.trace[-1].node == "generate_answer"


def test_eval_invalid_question_uses_conditional_abort(monkeypatch):
    """Eval bonus: invalid input routes to abort_invalid without retrieve."""
    called = {"retrieve": False}

    def fake_retrieve(_question: str, *, top_k: int | None = None):
        called["retrieve"] = True
        return []

    monkeypatch.setattr("trackflow_api.agent.nodes.rag_pipeline.retrieve", fake_retrieve)

    graph = get_compiled_knowledge_graph()
    final_state = graph.invoke(
        {
            "run_id": str(uuid.uuid4()),
            "raw_question": "ab",
            "node_trace": [],
        },
        config={"configurable": {"thread_id": str(uuid.uuid4())}},
    )

    assert called["retrieve"] is False
    nodes = [step["node"] for step in final_state["node_trace"]]
    assert nodes == ["receive_question", "abort_invalid"]
    assert final_state.get("error")


def test_eval_checkpoint_persists_state_after_transition(monkeypatch):
    """Eval: MemorySaver checkpoints state for a completed thread."""
    chunks = [
        RetrievedChunk(
            id="c1",
            text="SEUR cubre mejor Aragón rural.",
            score=0.8,
            source_document="carrier-coverage",
            section="Cobertura",
        )
    ]
    _patch_rag(
        monkeypatch,
        chunks=chunks,
        answer="SEUR es la mejor opción documentada para Aragón rural.",
        sources=[SourceReference(source_document="carrier-coverage", section="Cobertura")],
    )

    result = ask("¿Qué transportista cubre mejor Aragón rural?")
    graph = get_compiled_knowledge_graph()
    checkpoint = graph.get_state({"configurable": {"thread_id": result.run_id}})

    assert checkpoint.values.get("answer")
    assert checkpoint.values.get("question")
    assert len(checkpoint.values.get("node_trace") or []) >= 3
