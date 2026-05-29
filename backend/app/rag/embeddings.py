"""
Embedding model wrapper.
Uses Sentence Transformers (all-MiniLM-L6-v2) for document and query embeddings.
"""

import logging
from typing import List, Optional

from app.config import settings

logger = logging.getLogger(__name__)

# Module-level cache for the embedding model
_embedding_model = None


def get_embedding_model():
    """
    Lazy-load and cache the SentenceTransformer embedding model.

    Returns:
        A HuggingFaceEmbeddings instance compatible with LangChain.
    """
    global _embedding_model

    if _embedding_model is not None:
        return _embedding_model

    logger.info("Loading embedding model: %s", settings.embedding_model)

    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings

        _embedding_model = HuggingFaceEmbeddings(
            model_name=settings.embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True, "batch_size": 64},
        )
        logger.info("Embedding model loaded successfully")
        return _embedding_model

    except Exception as exc:
        logger.error("Failed to load embedding model: %s", exc, exc_info=True)
        raise RuntimeError(f"Could not load embedding model: {exc}") from exc


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors.
    """
    model = get_embedding_model()
    return model.embed_documents(texts)


def embed_query(query: str) -> List[float]:
    """
    Generate embedding for a single query string.

    Args:
        query: The query text.

    Returns:
        Embedding vector.
    """
    model = get_embedding_model()
    return model.embed_query(query)
