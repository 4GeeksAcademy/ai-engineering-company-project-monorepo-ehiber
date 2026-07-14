import pytest

from trackflow_api.rag import embed


def test_embed_texts_returns_expected_dimension(monkeypatch):
    monkeypatch.setenv("RAG_EMBEDDING_DIMENSION", "4")

    def fake_create_embeddings(texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3, 0.4] for _ in texts]

    monkeypatch.setattr(embed, "create_embeddings", fake_create_embeddings)

    vectors = embed.embed_texts(["hola", "mundo"])
    assert len(vectors) == 2
    assert len(vectors[0]) == 4


def test_embed_query_returns_single_vector(monkeypatch):
    monkeypatch.setenv("RAG_EMBEDDING_DIMENSION", "3")

    def fake_create_embeddings(texts: list[str]) -> list[list[float]]:
        assert texts == ["pregunta"]
        return [[1.0, 2.0, 3.0]]

    monkeypatch.setattr(embed, "create_embeddings", fake_create_embeddings)

    vector = embed.embed_query("pregunta")
    assert vector == [1.0, 2.0, 3.0]
