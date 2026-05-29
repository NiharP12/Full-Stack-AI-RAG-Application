"""
FAISS vector store manager.
Handles creating, loading, saving, and querying the FAISS index.
"""

import logging
import os
import threading
from typing import Dict, List, Optional, Tuple

from app.config import settings

logger = logging.getLogger(__name__)

# Thread lock for safe concurrent access
_lock = threading.Lock()

# Module-level singleton
_vector_store = None


class VectorStoreManager:
    """Manages the FAISS vector store lifecycle."""

    def __init__(self):
        self.store_path = settings.vector_store_path
        self.index_name = "rag_index"
        self._store = None

    def load_or_create(self) -> None:
        """Load an existing FAISS index from disk, or create a new one."""
        global _vector_store

        index_file = os.path.join(self.store_path, f"{self.index_name}.faiss")

        if os.path.exists(index_file):
            try:
                from langchain_community.vectorstores import FAISS
                from app.rag.embeddings import get_embedding_model

                logger.info("Loading existing FAISS index from %s", self.store_path)
                self._store = FAISS.load_local(
                    self.store_path,
                    get_embedding_model(),
                    index_name=self.index_name,
                    allow_dangerous_deserialization=True,
                )
                _vector_store = self._store
                logger.info("FAISS index loaded successfully")
            except Exception as exc:
                logger.warning("Could not load FAISS index: %s — will create new on first ingest", exc)
                self._store = None
                _vector_store = None
        else:
            logger.info("No existing FAISS index found — will create on first document ingest")
            self._store = None
            _vector_store = None

    def add_documents(self, texts: List[str], metadatas: List[Dict]) -> int:
        """
        Add document chunks to the vector store.

        Args:
            texts: List of text chunks.
            metadatas: Corresponding metadata for each chunk.

        Returns:
            Number of chunks added.
        """
        global _vector_store

        from langchain_community.vectorstores import FAISS
        from app.rag.embeddings import get_embedding_model

        with _lock:
            if self._store is None and _vector_store is None:
                # Create new index from first batch
                logger.info("Creating new FAISS index with %d chunks", len(texts))
                self._store = FAISS.from_texts(
                    texts,
                    get_embedding_model(),
                    metadatas=metadatas,
                )
                _vector_store = self._store
            else:
                # Add to existing index
                store = self._store or _vector_store
                store.add_texts(texts, metadatas=metadatas)
                self._store = store
                _vector_store = store
                logger.info("Added %d chunks to existing FAISS index", len(texts))

            # Persist to disk
            self._save()

        return len(texts)

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict] = None,
    ) -> List[Tuple]:
        """
        Search for similar documents.

        Args:
            query: Search query string.
            k: Number of results to return.
            filter_dict: Optional metadata filter.

        Returns:
            List of (Document, score) tuples.
        """
        global _vector_store
        store = self._store or _vector_store

        if store is None:
            logger.warning("Vector store is empty — no documents ingested yet")
            return []

        try:
            results = store.similarity_search_with_score(query, k=k)
            logger.info("Similarity search returned %d results for query: %s...", len(results), query[:50])

            # Apply metadata filter if provided
            if filter_dict:
                filtered = []
                for doc, score in results:
                    match = all(
                        doc.metadata.get(key) == value
                        for key, value in filter_dict.items()
                    )
                    if match:
                        filtered.append((doc, score))
                return filtered

            return results

        except Exception as exc:
            logger.error("Similarity search error: %s", exc, exc_info=True)
            return []

    def delete_by_source(self, source: str) -> bool:
        """
        Delete all chunks from a specific source file.

        Note: FAISS doesn't support direct deletion, so we rebuild the index
        excluding the specified source.
        """
        global _vector_store
        store = self._store or _vector_store

        if store is None:
            return False

        try:
            # Get all documents
            all_docs = store.docstore._dict
            ids_to_keep = []
            texts_to_keep = []
            metas_to_keep = []

            for doc_id, doc in all_docs.items():
                if doc.metadata.get("source") != source:
                    texts_to_keep.append(doc.page_content)
                    metas_to_keep.append(doc.metadata)

            if len(texts_to_keep) == len(all_docs):
                logger.warning("No documents found with source: %s", source)
                return False

            # Rebuild index without the deleted source
            if texts_to_keep:
                from langchain_community.vectorstores import FAISS
                from app.rag.embeddings import get_embedding_model

                with _lock:
                    self._store = FAISS.from_texts(
                        texts_to_keep,
                        get_embedding_model(),
                        metadatas=metas_to_keep,
                    )
                    _vector_store = self._store
                    self._save()
            else:
                # No documents left — reset
                self._store = None
                _vector_store = None
                self._delete_index_files()

            logger.info("Deleted chunks for source: %s", source)
            return True

        except Exception as exc:
            logger.error("Delete by source error: %s", exc, exc_info=True)
            return False

    def delete_all(self) -> None:
        """Delete the entire vector store."""
        global _vector_store

        with _lock:
            self._store = None
            _vector_store = None
            self._delete_index_files()
            logger.info("Vector store cleared")

    def get_document_count(self) -> int:
        """Return the number of chunks in the store."""
        global _vector_store
        store = self._store or _vector_store
        if store is None:
            return 0
        try:
            return len(store.docstore._dict)
        except Exception:
            return 0

    def _save(self) -> None:
        """Persist the FAISS index to disk."""
        if self._store is not None:
            os.makedirs(self.store_path, exist_ok=True)
            self._store.save_local(self.store_path, index_name=self.index_name)
            logger.debug("FAISS index saved to %s", self.store_path)

    def _delete_index_files(self) -> None:
        """Remove index files from disk."""
        for ext in [".faiss", ".pkl"]:
            path = os.path.join(self.store_path, f"{self.index_name}{ext}")
            if os.path.exists(path):
                os.remove(path)
