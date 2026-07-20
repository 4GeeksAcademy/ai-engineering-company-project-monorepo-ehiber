from fastapi.testclient import TestClient

from trackflow_api.rag.types import QueryResult, RetrievedChunk, SourceReference


def _client() -> TestClient:
    from trackflow_api.main import app

    return TestClient(app)


def test_knowledge_ask_returns_generated_answer_via_graph(monkeypatch):
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
            sources=[
                SourceReference(
                    source_document="carrier-coverage",
                    section="Cobertura de Transportistas",
                )
            ],
        )

    monkeypatch.setattr("data.pipelines.rag.retrieve", fake_retrieve)
    monkeypatch.setattr("data.pipelines.rag.query", fake_query)
    monkeypatch.setattr("trackflow_api.agent.nodes.rag_pipeline.retrieve", fake_retrieve)
    monkeypatch.setattr("trackflow_api.agent.nodes.rag_pipeline.query", fake_query)

    response = _client().post(
        "/api/knowledge/ask",
        json={"question": "¿qué transportista cubre mejor Aragón rural?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Para Aragón rural recomendamos SEUR por su cobertura documentada."
    assert body["answer"] != "SEUR: mejor cobertura en zonas rurales de Aragón."
    assert body["run_id"]
    assert body["checkpointed"] is True
    assert [step["node"] for step in body["trace"]] == [
        "receive_question",
        "retrieve",
        "generate_answer",
    ]
    assert body["sources"] == [
        {
            "source_document": "carrier-coverage",
            "section": "Cobertura de Transportistas",
        }
    ]

    trace_response = _client().get(f"/api/knowledge/runs/{body['run_id']}")
    assert trace_response.status_code == 200
    assert trace_response.json()["run_id"] == body["run_id"]


def test_knowledge_ask_validates_question_length():
    response = _client().post("/api/knowledge/ask", json={"question": "ab"})
    assert response.status_code in {400, 422}
