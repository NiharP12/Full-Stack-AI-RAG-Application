"""
Text chunking module.
Uses LangChain's RecursiveCharacterTextSplitter with configurable size and overlap.
"""

import logging
from typing import Dict, List, Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.config import settings

logger = logging.getLogger(__name__)


class TextChunker:
    """Splits documents into overlapping chunks for embedding."""

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
            is_separator_regex=False,
        )

        logger.info(
            "TextChunker initialised — chunk_size=%d, overlap=%d",
            self.chunk_size,
            self.chunk_overlap,
        )

    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Split text into chunks with metadata.

        Args:
            text: The full document text.
            metadata: Base metadata to attach to each chunk (e.g. filename, page).

        Returns:
            List of dicts with ``content`` and ``metadata`` keys.
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to chunker")
            return []

        base_meta = metadata or {}
        chunks = self.splitter.split_text(text)

        result = []
        for i, chunk_text in enumerate(chunks):
            chunk_meta = {
                **base_meta,
                "chunk_index": i,
                "chunk_total": len(chunks),
            }
            result.append({
                "content": chunk_text,
                "metadata": chunk_meta,
            })

        logger.info(
            "Split text into %d chunks (source: %s)",
            len(result),
            base_meta.get("source", "unknown"),
        )
        return result

    def chunk_pages(
        self,
        pages: List[Dict],
        base_metadata: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Chunk a list of page dicts (each with ``text`` and optional ``page`` keys).

        Useful for PDFs where each page is extracted separately.

        Args:
            pages: List of dicts with at least a ``text`` key.
            base_metadata: Metadata shared across all pages.

        Returns:
            List of chunk dicts.
        """
        all_chunks = []
        base_meta = base_metadata or {}

        for page_data in pages:
            page_text = page_data.get("text", "")
            page_num = page_data.get("page")

            page_meta = {**base_meta}
            if page_num is not None:
                page_meta["page"] = page_num

            chunks = self.chunk_text(page_text, metadata=page_meta)
            all_chunks.extend(chunks)

        return all_chunks
