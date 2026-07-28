from uuid import uuid4

from fastapi.testclient import TestClient

from trackflow_api.rag.types import QueryResult, RetrievedChunk, SourceReference


def _client() -> TestClient:
    from trackflow_api.main import app

    return TestClient(app)


def _auth_headers(client: TestClient) -> dict[str, str]:
    email = f"knowledge-{uuid4().hex[:8]}@trackflow.com"
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "securepass123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_knowledge_ask_requires_authentication():
    response = _client().post(
        "/api/knowledge/ask",
        json={"question": "¿qué transportista cubre mejor Aragón rural?"},
    )
    assert response.status_code == 401


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

    def fake_query(_question: str, chunks, *, policy_country_lock=None):
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

    client = _client()
    headers = _auth_headers(client)
    response = client.post(
        "/api/knowledge/ask",
        json={"question": "¿qué transportista cubre mejor Aragón rural?"},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Para Aragón rural recomendamos SEUR por su cobertura documentada."
    assert body["answer"] != "SEUR: mejor cobertura en zonas rurales de Aragón."
    assert body["run_id"]
    assert body["checkpointed"] is True
    assert [step["node"] for step in body["trace"]] == [
        "receive_question",
        "guard_input",
        "authorize_tracking",
        "classify_intent",
        "retrieve",
        "generate_answer",
    ]
    assert body["sources"] == [
        {
            "source_document": "carrier-coverage",
            "section": "Cobertura de Transportistas",
        }
    ]

    trace_response = client.get(f"/api/knowledge/runs/{body['run_id']}", headers=headers)
    assert trace_response.status_code == 200
    assert trace_response.json()["run_id"] == body["run_id"]

    stats_response = client.get("/api/knowledge/guardrails/stats", headers=headers)
    assert stats_response.status_code == 200
    assert "by_failure_type" in stats_response.json()
    assert "total" in stats_response.json()


def test_knowledge_ask_validates_question_length():
    client = _client()
    headers = _auth_headers(client)
    response = client.post(
        "/api/knowledge/ask",
        json={"question": "ab"},
        headers=headers,
    )
    assert response.status_code in {400, 422}
