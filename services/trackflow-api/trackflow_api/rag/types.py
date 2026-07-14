from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class KnowledgeChunk:
    id: str
    text: str
    source_document: str
    section: str
    language: str
    chunk_index: int


@dataclass(frozen=True)
class RetrievedChunk:
    id: str
    text: str
    score: float
    source_document: str
    section: str


@dataclass(frozen=True)
class SourceReference:
    source_document: str
    section: str


@dataclass(frozen=True)
class QueryResult:
    answer: str
    sources: list[SourceReference] = field(default_factory=list)


@dataclass(frozen=True)
class SetupResult:
    documents_indexed: int
    chunks_indexed: int
    collection_name: str
