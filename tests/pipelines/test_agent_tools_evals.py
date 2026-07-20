"""Agent uses MCP client (not direct incident/inventory services) + classify_intent routing."""

from __future__ import annotations

import pytest

from trackflow_api.agent.graph import reset_compiled_knowledge_graph
from trackflow_api.agent.nodes import classify_intent
from trackflow_api.agent.tracing import clear_traces
from trackflow_api.rag.types import QueryResult, RetrievedChunk, SourceReference
from trackflow_api.services.rag_service import ask


@pytest.fixture(autouse=True)
def _reset_agent_runtime():
    reset_compiled_knowledge_graph()
    clear_traces()
    yield
    reset_compiled_knowledge_graph()
    clear_traces()


def test_eval_intent_router_chooses_incident_without_user_hint():
    assert classify_intent("¿Cuál es el estado de la incidencia 12?") == "incident"
    assert classify_intent("status del ticket 482") == "incident"


def test_eval_intent_router_keeps_policy_questions_on_rag():
    assert classify_intent("¿Cuál es la ventana de devolución estándar?") == "rag"
    assert classify_intent("¿Qué transportista cubre Aragón rural?") == "rag"


def test_eval_incident_question_uses_mcp_tool_not_rag(monkeypatch):
    """Eval: incident questions hit tool_incidents via MCP bridge and skip retrieve."""
    called = {"retrieve": False, "mcp": False}

    def fake_retrieve(_question: str, *, top_k: int | None = None):
        called["retrieve"] = True
        return []

    def fake_mcp(tool_name: str, arguments=None):
        called["mcp"] = True
        assert tool_name == "get_incident"
        assert arguments and (arguments.get("incident_id") == 12 or "12" in str(arguments))
        return {
            "ok": True,
            "found": True,
            "incident": {
                "id": 12,
                "title": "Retraso en entrega",
                "status": "in_progress",
                "category": "delivery_delay",
                "branch": "zaragoza_warehouse",
            },
        }

    def fake_completion(*, system_prompt: str, user_prompt: str) -> str:
        assert "in_progress" in user_prompt or "12" in user_prompt
        return "La incidencia 12 está en progreso (in_progress) en el almacén de Zaragoza."

    monkeypatch.setattr("trackflow_api.agent.nodes.rag_pipeline.retrieve", fake_retrieve)
    monkeypatch.setattr(
        "trackflow_api.agent.tools.incidents_inventory.call_mcp_tool",
        fake_mcp,
    )
    monkeypatch.setattr("trackflow_api.agent.nodes.create_completion", fake_completion)

    result = ask("¿Cuál es el estado de la incidencia 12?")
    nodes = [step.node for step in result.trace]

    assert called["retrieve"] is False
    assert called["mcp"] is True
    assert "classify_intent" in nodes
    assert "tool_incidents" in nodes
    assert "generate_from_tool" in nodes
    assert "retrieve" not in nodes
    assert "12" in result.answer or "progreso" in result.answer.lower()


def test_eval_policy_question_still_uses_rag(monkeypatch):
    chunks = [
        RetrievedChunk(
            id="c1",
            text="Ventana de devolución estándar: 30 días desde la entrega.",
            score=0.9,
            source_document="returns-policy",
            section="Política de Devoluciones",
        )
    ]

    def fake_retrieve(_question: str, *, top_k: int | None = None):
        return chunks

    def fake_query(_question: str, retrieved):
        return QueryResult(
            answer="La ventana estándar es de 30 días desde la entrega.",
            sources=[
                SourceReference(
                    source_document="returns-policy",
                    section="Política de Devoluciones",
                )
            ],
        )

    monkeypatch.setattr("trackflow_api.agent.nodes.rag_pipeline.retrieve", fake_retrieve)
    monkeypatch.setattr("trackflow_api.agent.nodes.rag_pipeline.query", fake_query)

    result = ask("¿Cuál es la ventana de devolución estándar?")
    nodes = [step.node for step in result.trace]
    assert "retrieve" in nodes
    assert "tool_incidents" not in nodes
    assert "generate_answer" in nodes
    assert "30 días" in result.answer


def test_eval_tool_failure_uses_recovery_path(monkeypatch):
    def fake_mcp(_tool_name: str, _arguments=None):
        return {
            "ok": False,
            "error": "service_unavailable",
            "message": "El servidor MCP de incidencias no respondió.",
        }

    def fake_completion(*, system_prompt: str, user_prompt: str) -> str:
        assert "service_unavailable" in user_prompt or "no respondió" in user_prompt.lower()
        return (
            "No pude consultar el gestor de incidencias en este momento. "
            "Reintenta en unos minutos o escala al equipo interno."
        )

    monkeypatch.setattr(
        "trackflow_api.agent.tools.incidents_inventory.call_mcp_tool",
        fake_mcp,
    )
    monkeypatch.setattr("trackflow_api.agent.nodes.create_completion", fake_completion)

    result = ask("¿Estado del ticket 482?")
    nodes = [step.node for step in result.trace]
    assert "tool_incidents" in nodes
    assert "tool_recovery" in nodes
    assert "generate_from_tool" in nodes
    assert "no pude" in result.answer.lower() or "reintenta" in result.answer.lower()


def test_eval_inventory_question_uses_mcp_inventory_tool(monkeypatch):
    def fake_mcp(tool_name: str, arguments=None):
        assert tool_name == "query_inventory"
        return {
            "ok": True,
            "found": True,
            "sku": "TF-ELEC-0010",
            "warehouse": "LA",
            "items": [
                {
                    "sku": "TF-ELEC-0010",
                    "warehouse": "LA",
                    "current_stock": 42,
                    "name": "Auriculares",
                }
            ],
        }

    def fake_completion(*, system_prompt: str, user_prompt: str) -> str:
        assert "42" in user_prompt
        return "Hay 42 unidades de TF-ELEC-0010 en el almacén LA."

    monkeypatch.setattr(
        "trackflow_api.agent.tools.incidents_inventory.call_mcp_tool",
        fake_mcp,
    )
    monkeypatch.setattr("trackflow_api.agent.nodes.create_completion", fake_completion)

    result = ask("¿Hay stock del SKU TF-ELEC-0010 en LA?")
    nodes = [step.node for step in result.trace]
    assert "tool_inventory" in nodes
    assert "retrieve" not in nodes
    assert "42" in result.answer


def test_agent_tools_module_does_not_import_services_directly():
    """Guardrail: tool nodes go through MCP — no direct service imports in incidents_inventory."""
    import inspect

    import trackflow_api.agent.tools.incidents_inventory as mod

    source = inspect.getsource(mod)
    assert "incident_manager_service" not in source
    assert "inventory_query_service" not in source
    assert "call_mcp_tool" in source
