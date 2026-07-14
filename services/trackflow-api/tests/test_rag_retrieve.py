from trackflow_api.rag.retrieve import retrieve
from trackflow_api.rag.types import RetrievedChunk


def test_retrieve_maps_qdrant_hits(monkeypatch):
    def fake_embed_query(_question: str) -> list[float]:
        return [0.5, 0.5, 0.5]

    class FakeHit:
        def __init__(self) -> None:
            self.id = "chunk-1"
            self.score = 0.91
            self.payload = {
                "text": "Ventana de devolución estándar: 30 días",
                "source_document": "returns-policy",
                "section": "Política de Devoluciones",
            }

    class FakeClient:
        def query_points(self, **_kwargs):
            class Response:
                points = [FakeHit()]

            return Response()

    monkeypatch.setattr("trackflow_api.rag.retrieve.embed_query", fake_embed_query)
    monkeypatch.setattr(
        "trackflow_api.rag.retrieve.get_qdrant_client",
        lambda: FakeClient(),
    )

    chunks = retrieve("¿cuál es la ventana de devolución estándar?", top_k=3)
    assert chunks == [
        RetrievedChunk(
            id="chunk-1",
            text="Ventana de devolución estándar: 30 días",
            score=0.91,
            source_document="returns-policy",
            section="Política de Devoluciones",
        )
    ]
