from trackflow_api.rag.query import SYSTEM_PROMPT, query
from trackflow_api.rag.types import RetrievedChunk


def test_query_always_calls_completion_and_returns_generated_answer(monkeypatch):
    captured: dict[str, str] = {}

    def fake_create_completion(*, system_prompt: str, user_prompt: str) -> str:
        captured["system_prompt"] = system_prompt
        captured["user_prompt"] = user_prompt
        return "La ventana estándar es de 30 días desde la entrega."

    monkeypatch.setattr(
        "trackflow_api.rag.query.create_completion",
        fake_create_completion,
    )

    chunks = [
        RetrievedChunk(
            id="chunk-1",
            text="Ventana de devolución estándar: 30 días desde la entrega",
            score=0.9,
            source_document="returns-policy",
            section="Política de Devoluciones",
        )
    ]

    result = query("¿cuál es la ventana de devolución estándar?", chunks)

    assert result.answer == "La ventana estándar es de 30 días desde la entrega."
    assert result.answer != chunks[0].text
    assert result.sources[0].source_document == "returns-policy"
    assert captured["system_prompt"] == SYSTEM_PROMPT
    assert "30 días" in captured["user_prompt"]


def test_query_handles_empty_context_with_completion(monkeypatch):
    called = {"value": False}

    def fake_create_completion(*, system_prompt: str, user_prompt: str) -> str:
        called["value"] = True
        assert "sin contexto relevante" in user_prompt
        return "Necesito confirmar esa condicion con el equipo interno."

    monkeypatch.setattr(
        "trackflow_api.rag.query.create_completion",
        fake_create_completion,
    )

    result = query("hay descuento especial no documentado?", [])
    assert called["value"] is True
    assert "confirmar" in result.answer.lower()
    assert result.sources == []
