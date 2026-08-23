"""
Pydantic data contracts for PII-001 RAG Retrieval Engine (SP-005)
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """Represents an indexed text passage snippet from a source document."""
    chunk_id: str = Field(description="Unique identifier for chunk")
    doc_id: str = Field(description="Parent document identifier")
    source_title: str = Field(description="Title or filename of source document")
    content: str = Field(description="Text snippet of the chunk")
    chunk_index: int = Field(description="0-indexed position within parent document")
    start_char: int = Field(description="Starting character index in parent document")
    end_char: int = Field(description="Ending character index in parent document")


class RetrievedContext(BaseModel):
    """Represents a retrieved passage with relevance scoring and citation tag."""
    chunk_id: str = Field(description="Chunk ID")
    source_title: str = Field(description="Source document title")
    content: str = Field(description="Text snippet content")
    relevance_score: float = Field(description="BM25 / TF-IDF match score")
    citation_tag: str = Field(description="Formatted citation anchor tag e.g. [Source: Title #Chunk_2]")


class RAGQueryRequest(BaseModel):
    """Query payload for retrieving evidence passages."""
    query_id: str = Field(description="Unique query identifier")
    query_text: str = Field(description="Search or interview topic query text")
    top_k: int = Field(default=3, ge=1, le=10, description="Maximum number of context passages to return")


class RAGQueryResponse(BaseModel):
    """Container for retrieved context passages and search metrics."""
    query_id: str = Field(description="Query ID")
    query_text: str = Field(description="Original search query text")
    retrieved_contexts: List[RetrievedContext] = Field(default_factory=list)
    total_chunks_searched: int = Field(description="Total chunks in indexed corpus")
    retrieval_time_ms: float = Field(description="Retrieval latency in milliseconds")
