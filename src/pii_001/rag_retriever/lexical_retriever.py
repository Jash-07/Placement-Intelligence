"""
Lexical BM25/TF-IDF RAG Retriever Engine for PII-001 (SP-005)

Indexes text chunks, ranks evidence passages against queries, and grounds results with citation tags.
"""

import math
import re
import time
import uuid
from typing import List, Dict, Set, Tuple, Optional
from pii_001.rag_retriever.schemas import (
    DocumentChunk,
    RetrievedContext,
    RAGQueryRequest,
    RAGQueryResponse,
)

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "is", "are", "was", "were",
    "be", "been", "being", "in", "on", "at", "to", "for", "with", "by",
    "about", "against", "between", "into", "through", "during", "before",
    "after", "above", "below", "to", "from", "up", "down", "in", "out",
    "on", "off", "over", "under", "again", "further", "then", "once",
    "this", "that", "these", "those", "how", "what", "which", "who", "whom",
}

TOKEN_PATTERN = re.compile(r"\b\w+\b")


def tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric tokens excluding standard stop words."""
    tokens = TOKEN_PATTERN.findall(text.lower())
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]


class LexicalRetriever:
    """
    Deterministic BM25-style Lexical Retriever.
    Indexes DocumentChunk objects and ranks passages by query relevance.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.chunks: List[DocumentChunk] = []
        self.chunk_tokens: List[List[str]] = []
        self.doc_freqs: Dict[str, int] = {}
        self.avg_doc_len: float = 0.0

    def index_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Build term frequency and inverse document frequency index across chunks."""
        self.chunks = chunks
        self.chunk_tokens = []
        self.doc_freqs = {}

        total_len = 0
        for chunk in chunks:
            tokens = tokenize(chunk.content)
            self.chunk_tokens.append(tokens)
            total_len += len(tokens)

            unique_terms = set(tokens)
            for term in unique_terms:
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

        num_docs = len(chunks)
        self.avg_doc_len = (total_len / num_docs) if num_docs > 0 else 1.0

    def query(self, query_text: str, top_k: int = 3) -> RAGQueryResponse:
        """
        Execute BM25 query against indexed corpus and return RAGQueryResponse.
        """
        start_time = time.perf_counter()
        query_id = str(uuid.uuid4())

        if not self.chunks or not query_text.strip():
            return RAGQueryResponse(
                query_id=query_id,
                query_text=query_text,
                retrieved_contexts=[],
                total_chunks_searched=len(self.chunks),
                retrieval_time_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
            )

        query_tokens = tokenize(query_text)
        num_docs = len(self.chunks)
        scores: List[Tuple[float, DocumentChunk]] = []

        for idx, chunk in enumerate(self.chunks):
            doc_tokens = self.chunk_tokens[idx]
            doc_len = len(doc_tokens)
            if doc_len == 0:
                continue

            tf_map: Dict[str, int] = {}
            for t in doc_tokens:
                tf_map[t] = tf_map.get(t, 0) + 1

            score = 0.0
            for qt in query_tokens:
                if qt in tf_map:
                    doc_freq = self.doc_freqs.get(qt, 0)
                    # BM25 IDF score calculation
                    idf = math.log((num_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0)
                    tf = tf_map[qt]

                    # BM25 term score scaling
                    numerator = tf * (self.k1 + 1.0)
                    denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                    score += idf * (numerator / denominator)

            if score > 0.0:
                scores.append((round(score, 3), chunk))

        # Sort by relevance score descending
        scores.sort(key=lambda x: x[0], reverse=True)

        top_matches = scores[:top_k]
        retrieved_contexts: List[RetrievedContext] = []

        for rel_score, chunk in top_matches:
            citation_tag = f"[Source: {chunk.source_title} #{chunk.chunk_index + 1}]"
            retrieved_contexts.append(
                RetrievedContext(
                    chunk_id=chunk.chunk_id,
                    source_title=chunk.source_title,
                    content=chunk.content,
                    relevance_score=rel_score,
                    citation_tag=citation_tag,
                )
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return RAGQueryResponse(
            query_id=query_id,
            query_text=query_text,
            retrieved_contexts=retrieved_contexts,
            total_chunks_searched=len(self.chunks),
            retrieval_time_ms=round(elapsed_ms, 2),
        )
