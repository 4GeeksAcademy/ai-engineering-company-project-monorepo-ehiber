from trackflow_api.rag.setup import chunk_documents, load_source_documents
from trackflow_api.core.config import get_settings


def test_load_source_documents_reads_all_four_files():
    settings = get_settings()
    documents = load_source_documents(settings.rag_knowledge_source_path)
    assert len(documents) == 4
    source_ids = {source for source, _ in documents}
    assert source_ids == {
        "sla-delivery",
        "returns-policy",
        "carrier-coverage",
        "storage-pricing",
    }


def test_chunk_documents_produces_minimum_chunks_per_document():
    settings = get_settings()
    documents = load_source_documents(settings.rag_knowledge_source_path)
    chunks = chunk_documents(documents)

    assert len(chunks) >= 12
    for source_document in {
        "sla-delivery",
        "returns-policy",
        "carrier-coverage",
        "storage-pricing",
    }:
        document_chunks = [chunk for chunk in chunks if chunk.source_document == source_document]
        assert len(document_chunks) >= 3
        assert all(chunk.language == "es" for chunk in document_chunks)
        assert all(chunk.text.strip() for chunk in document_chunks)
