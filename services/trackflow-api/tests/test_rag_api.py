from fastapi.testclient import TestClient


def _client() -> TestClient:
    from trackflow_api.main import app

    return TestClient(app)


def test_knowledge_ask_returns_generated_answer(monkeypatch):
    from trackflow_api.rag.types import QueryResult, RetrievedChunk, SourceReference

    def fake_retrieve(_question: str, *, top_k: int | None = None):
        return [
            RetrievedChunk(
                id="chunk-1",
                text="SEUR: mejor cobertura en zonas rurales de Aragón.",
                score=0.88,
                source_document="carrier-coverage",
                section="Cobertura de Transportistas",
            )
        ]

    def fake_query(_question: str, chunks):
        assert len(chunks) == 1
        return QueryResult(
            answer="Para Aragón rural recomendamos SEUR por su cobertura documentada.",
            sources=[SourceReference(source_document="carrier-coverage", section="Cobertura de Transportistas")],
        )

    monkeypatch.setattr("trackflow_api.services.rag_service.retrieve", fake_retrieve)
    monkeypatch.setattr("trackflow_api.services.rag_service.query", fake_query)

    response = _client().post(
        "/api/knowledge/ask",
        json={"question": "¿qué transportista cubre mejor Aragón rural?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Para Aragón rural recomendamos SEUR por su cobertura documentada."
    assert body["answer"] != "SEUR: mejor cobertura en zonas rurales de Aragón."
    assert body["sources"] == [
        {
            "source_document": "carrier-coverage",
            "section": "Cobertura de Transportistas",
        }
    ]


def test_knowledge_ask_validates_question_length():
    response = _client().post("/api/knowledge/ask", json={"question": "ab"})
    assert response.status_code in {400, 422}
