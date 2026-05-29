"""
Semantic retriever — searches the vector store and re-ranks results.
"""

import logging
from typing import Dict, List, Optional

from app.config import settings
from app.rag.vectorstore import VectorStoreManager

logger = logging.getLogger(__name__)


class SemanticRetriever:
    """Retrieves relevant document chunks via similarity search with optional re-ranking."""

    def __init__(self):
        self.vs_manager = VectorStoreManager()
        # Reload the in-memory store if it's been loaded by startup
        self.vs_manager.load_or_create()

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_source: Optional[str] = None,
    ) -> Dict:
        """
        Retrieve the most relevant chunks for a query.

        Args:
            query: User's question.
            top_k: Number of results to retrieve.
            filter_source: Optional filename filter.

        Returns:
            Dict with ``chunks`` (list of text strings) and
            ``sources`` (list of metadata dicts with score).
        """
        k = top_k or settings.top_k_results
        filter_dict = {"source": filter_source} if filter_source else None

        results = self.vs_manager.similarity_search(query, k=k, filter_dict=filter_dict)

        if not results:
            logger.info("No results found for query: %s", query[:80])
            return {"chunks": [], "sources": []}

        # Re-rank: sort by score (lower = more similar in FAISS L2)
        sorted_results = sorted(results, key=lambda x: x[1])

        # Filter by similarity threshold
        threshold = settings.similarity_threshold
        chunks = []
        sources = []

        for doc, score in sorted_results:
            # FAISS L2 distance: lower = better.  Normalised embeddings → score ∈ [0, 2]
            # We convert to a 0-1 similarity: sim = 1 - (score / 2)
            similarity = max(0.0, 1.0 - (score / 2.0))

            if similarity < threshold:
                continue

            chunks.append(doc.page_content)
            sources.append({
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "page": doc.metadata.get("page"),
                "chunk_index": doc.metadata.get("chunk_index"),
                "score": round(similarity, 4),
            })

        logger.info(
            "Retrieved %d chunks above threshold %.2f for: %s",
            len(chunks),
            threshold,
            query[:80],
        )

        return {"chunks": chunks, "sources": sources}
