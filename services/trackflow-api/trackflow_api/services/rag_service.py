from __future__ import annotations

from ..rag.query import query
from ..rag.retrieve import retrieve
from ..schemas.knowledge import AskResponse, SourceReferenceResponse


def ask(question: str) -> AskResponse:
    chunks = retrieve(question)
    result = query(question, chunks)
    return AskResponse(
        answer=result.answer,
        sources=[
            SourceReferenceResponse(
                source_document=source.source_document,
                section=source.section,
            )
            for source in result.sources
        ],
    )
