"""Reusable Milestone 7 RAG functions exposed for pipeline/agent orchestration.

These wrappers import the existing TrackFlow API implementations — they do not
rewrite embed / retrieve / query from scratch.
"""

from __future__ import annotations

from trackflow_api.rag.embed import embed_query, embed_texts
from trackflow_api.rag.query import query
from trackflow_api.rag.retrieve import retrieve
from trackflow_api.rag.types import QueryResult, RetrievedChunk, SourceReference

__all__ = [
    "embed_query",
    "embed_texts",
    "query",
    "retrieve",
    "QueryResult",
    "RetrievedChunk",
    "SourceReference",
]
