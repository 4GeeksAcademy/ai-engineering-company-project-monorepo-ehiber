from __future__ import annotations

from .litellm_client import create_embeddings


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return create_embeddings(texts)


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
