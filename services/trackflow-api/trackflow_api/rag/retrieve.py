from __future__ import annotations

from ..core.config import get_settings
from .embed import embed_query
from .qdrant_client import get_qdrant_client
from .types import RetrievedChunk


def retrieve(question: str, *, top_k: int | None = None) -> list[RetrievedChunk]:
    settings = get_settings()
    limit = top_k or settings.rag_top_k
    query_vector = embed_query(question)
    client = get_qdrant_client()
    hits = client.query_points(
        collection_name=settings.qdrant_collection,
        query=query_vector,
        limit=limit,
        with_payload=True,
    ).points

    chunks: list[RetrievedChunk] = []
    for hit in hits:
        payload = hit.payload or {}
        chunks.append(
            RetrievedChunk(
                id=str(hit.id),
                text=str(payload.get("text", "")),
                score=float(hit.score or 0.0),
                source_document=str(payload.get("source_document", "")),
                section=str(payload.get("section", "")),
            )
        )
    return chunks
