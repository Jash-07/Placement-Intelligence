"""
Unit tests for RAG Retrieval & Document Chunker Engine (SP-005)
"""

import pytest
from pii_001.rag_retriever.document_chunker import DocumentChunker
from pii_001.rag_retriever.lexical_retriever import LexicalRetriever
from pii_001.rag_retriever.schemas import RAGQueryResponse


def test_document_chunker_overlap(sample_company_prep_text: str):
    """Verify document chunking with character overlap and offset boundaries."""
    chunker = DocumentChunker(chunk_size=200, overlap=40)
    chunks = chunker.chunk_text(sample_company_prep_text, source_title="TechCorp_Prep_Guide.md", doc_id="doc_101")

    assert len(chunks) >= 3
    assert chunks[0].doc_id == "doc_101"
    assert chunks[0].source_title == "TechCorp_Prep_Guide.md"
    assert chunks[0].chunk_index == 0
    assert chunks[1].chunk_index == 1
    assert chunks[0].end_char > chunks[1].start_char  # Overlap verified


def test_lexical_retriever_bm25_search(sample_company_prep_text: str):
    """Verify BM25 retrieval query ranking and citation tagging."""
    chunker = DocumentChunker(chunk_size=300, overlap=50)
    chunks = chunker.chunk_text(sample_company_prep_text, source_title="TechCorp_Prep_Guide.md")

    retriever = LexicalRetriever()
    retriever.index_chunks(chunks)

    # Search for system design and PostgreSQL interview questions
    response: RAGQueryResponse = retriever.query("PostgreSQL database indexing and system design", top_k=2)

    assert response.total_chunks_searched == len(chunks)
    assert len(response.retrieved_contexts) == 2
    assert response.retrieval_time_ms < 20.0

    top_result = response.retrieved_contexts[0]
    assert top_result.relevance_score > 0.0
    assert "[Source: TechCorp_Prep_Guide.md #" in top_result.citation_tag
    assert any(term in top_result.content.lower() for term in ["postgresql", "system", "design"])


def test_empty_query_and_corpus():
    """Verify graceful handling of empty query or unindexed corpus."""
    retriever = LexicalRetriever()
    response = retriever.query("Python backend")

    assert response.total_chunks_searched == 0
    assert len(response.retrieved_contexts) == 0
