"""
Document Chunker Engine for PII-001 RAG Retrieval (SP-005)

Segments source text documents into sliding-window passages with overlap and metadata.
"""

import uuid
from typing import List
from pii_001.rag_retriever.schemas import DocumentChunk


class DocumentChunker:
    """Sliding window document chunker for RAG retrieval indexing."""

    def __init__(self, chunk_size: int = 300, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str, source_title: str = "Document", doc_id: str = "") -> List[DocumentChunk]:
        """
        Split raw document text into DocumentChunk objects with overlap.
        """
        if not text or not text.strip():
            return []

        doc_identifier = doc_id or str(uuid.uuid4())
        cleaned_text = " ".join(text.split())
        text_length = len(cleaned_text)

        chunks: List[DocumentChunk] = []
        step = self.chunk_size - self.overlap
        start = 0
        chunk_idx = 0

        while start < text_length:
            end = min(start + self.chunk_size, text_length)

            # If not at document end, try breaking at nearest space
            if end < text_length:
                space_pos = cleaned_text.rfind(" ", start, end)
                if space_pos > start + (self.chunk_size // 2):
                    end = space_pos

            snippet = cleaned_text[start:end].strip()
            if snippet:
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{doc_identifier}_{chunk_idx}",
                        doc_id=doc_identifier,
                        source_title=source_title,
                        content=snippet,
                        chunk_index=chunk_idx,
                        start_char=start,
                        end_char=end,
                    )
                )
                chunk_idx += 1

            start += step

        return chunks
