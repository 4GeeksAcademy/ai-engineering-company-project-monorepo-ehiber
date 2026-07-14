from __future__ import annotations

import re
import uuid
from pathlib import Path

from qdrant_client.http import models as qmodels

from ..core.config import get_settings
from .embed import embed_texts
from .qdrant_client import get_qdrant_client
from .types import KnowledgeChunk, SetupResult

SOURCE_FILES: dict[str, str] = {
    "trackflow-sla-delivery.es.md": "sla-delivery",
    "trackflow-returns-policy.es.md": "returns-policy",
    "trackflow-carrier-coverage.es.md": "carrier-coverage",
    "trackflow-storage-pricing.es.md": "storage-pricing",
}

MIN_CHUNKS_PER_DOCUMENT = 3


def _split_paragraphs(text: str) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    return paragraphs or [text.strip()]


def _chunk_markdown(content: str, source_document: str) -> list[KnowledgeChunk]:
    lines = content.splitlines()
    sections: list[tuple[str, list[str]]] = []
    current_title = "General"
    current_lines: list[str] = []

    for line in lines:
        if line.startswith("# "):
            if current_lines:
                sections.append((current_title, current_lines))
            current_title = line[2:].strip()
            current_lines = [line]
            continue
        if line.startswith("## "):
            if current_lines:
                sections.append((current_title, current_lines))
            current_title = line[3:].strip()
            current_lines = [line]
            continue
        current_lines.append(line)

    if current_lines:
        sections.append((current_title, current_lines))

    if not sections:
        sections = [("General", lines)]

    raw_chunks: list[tuple[str, str]] = []
    for section_title, section_lines in sections:
        section_text = "\n".join(section_lines).strip()
        if not section_text:
            continue
        paragraphs = _split_paragraphs(section_text)
        if len(paragraphs) >= 2 and len(section_text) > 400:
            for index, paragraph in enumerate(paragraphs):
                raw_chunks.append((f"{section_title} ({index + 1})", paragraph))
        else:
            raw_chunks.append((section_title, section_text))

    while len(raw_chunks) < MIN_CHUNKS_PER_DOCUMENT:
        largest_index = max(range(len(raw_chunks)), key=lambda idx: len(raw_chunks[idx][1]))
        section_title, section_text = raw_chunks[largest_index]
        paragraphs = _split_paragraphs(section_text)
        if len(paragraphs) < 2:
            break
        midpoint = len(paragraphs) // 2
        first_half = "\n\n".join(paragraphs[:midpoint]).strip()
        second_half = "\n\n".join(paragraphs[midpoint:]).strip()
        raw_chunks[largest_index] = (f"{section_title} (1)", first_half)
        raw_chunks.insert(largest_index + 1, (f"{section_title} (2)", second_half))

    chunks: list[KnowledgeChunk] = []
    for index, (section, text) in enumerate(raw_chunks):
        chunk_id = str(
            uuid.uuid5(uuid.NAMESPACE_URL, f"trackflow:{source_document}:{index}:{text[:120]}")
        )
        chunks.append(
            KnowledgeChunk(
                id=chunk_id,
                text=text,
                source_document=source_document,
                section=section,
                language="es",
                chunk_index=index,
            )
        )
    return chunks


def load_source_documents(source_dir: Path) -> list[tuple[str, str]]:
    documents: list[tuple[str, str]] = []
    for filename, source_document in SOURCE_FILES.items():
        path = source_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Missing knowledge source document: {path}")
        documents.append((source_document, path.read_text(encoding="utf-8")))
    return documents


def chunk_documents(documents: list[tuple[str, str]]) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    for source_document, content in documents:
        document_chunks = _chunk_markdown(content, source_document)
        if len(document_chunks) < MIN_CHUNKS_PER_DOCUMENT:
            raise ValueError(
                f"Document '{source_document}' produced {len(document_chunks)} chunks; "
                f"expected at least {MIN_CHUNKS_PER_DOCUMENT}."
            )
        chunks.extend(document_chunks)
    return chunks


def ensure_collection(*, recreate: bool = False) -> None:
    settings = get_settings()
    client = get_qdrant_client()
    collection_name = settings.qdrant_collection

    if recreate and client.collection_exists(collection_name):
        client.delete_collection(collection_name)

    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=qmodels.VectorParams(
                size=settings.rag_embedding_dimension,
                distance=qmodels.Distance.COSINE,
            ),
        )


def upsert_chunks(chunks: list[KnowledgeChunk], vectors: list[list[float]]) -> int:
    settings = get_settings()
    client = get_qdrant_client()
    points = [
        qmodels.PointStruct(
            id=chunk.id,
            vector=vector,
            payload={
                "company": "trackflow",
                "source_document": chunk.source_document,
                "section": chunk.section,
                "language": chunk.language,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
            },
        )
        for chunk, vector in zip(chunks, vectors, strict=True)
    ]
    client.upsert(collection_name=settings.qdrant_collection, points=points)
    return len(points)


def setup_knowledge_base(*, recreate: bool = False) -> SetupResult:
    settings = get_settings()
    documents = load_source_documents(settings.rag_knowledge_source_path)
    chunks = chunk_documents(documents)
    ensure_collection(recreate=recreate)
    vectors = embed_texts([chunk.text for chunk in chunks])
    indexed = upsert_chunks(chunks, vectors)
    return SetupResult(
        documents_indexed=len(documents),
        chunks_indexed=indexed,
        collection_name=settings.qdrant_collection,
    )
