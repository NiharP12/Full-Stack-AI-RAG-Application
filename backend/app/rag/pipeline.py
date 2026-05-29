"""
RAG Pipeline — orchestrates retrieval and generation.
"""

import logging
from typing import Dict, Generator, List, Optional

from app.rag.chunker import TextChunker
from app.rag.embeddings import get_embedding_model
from app.rag.llm_provider import invoke_llm, stream_llm_response
from app.rag.prompts import QA_PROMPT_TEMPLATE, SYSTEM_PROMPT
from app.rag.retriever import SemanticRetriever
from app.rag.vectorstore import VectorStoreManager
from langchain.schema import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


class RAGPipeline:
    """End-to-end RAG pipeline: ingest → retrieve → generate."""

    def __init__(self):
        self.chunker = TextChunker()
        self.vs_manager = VectorStoreManager()
        self.retriever = SemanticRetriever()

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def ingest(self, text: str, metadata: Dict) -> int:
        """
        Ingest a document: chunk text → embed → store in vector DB.

        Args:
            text: Full document text.
            metadata: Document metadata (source, file_type, etc.).

        Returns:
            Number of chunks stored.
        """
        # Chunk
        chunks = self.chunker.chunk_text(text, metadata=metadata)
        if not chunks:
            logger.warning("No chunks produced for: %s", metadata.get("source", "unknown"))
            return 0

        # Extract texts and metadatas
        texts = [c["content"] for c in chunks]
        metas = [c["metadata"] for c in chunks]

        # Store (embedding happens inside FAISS.from_texts / add_texts)
        count = self.vs_manager.add_documents(texts, metas)
        logger.info("Ingested %d chunks for: %s", count, metadata.get("source", "unknown"))
        return count

    def ingest_pages(self, pages: List[Dict], metadata: Dict) -> int:
        """
        Ingest page-based documents (e.g. PDFs).

        Args:
            pages: List of {text, page} dicts.
            metadata: Shared document metadata.

        Returns:
            Number of chunks stored.
        """
        chunks = self.chunker.chunk_pages(pages, base_metadata=metadata)
        if not chunks:
            return 0

        texts = [c["content"] for c in chunks]
        metas = [c["metadata"] for c in chunks]
        count = self.vs_manager.add_documents(texts, metas)
        logger.info("Ingested %d page-based chunks for: %s", count, metadata.get("source", "unknown"))
        return count

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def retrieve(self, question: str, top_k: Optional[int] = None) -> Dict:
        """
        Retrieve relevant chunks for a question.

        Returns:
            Dict with ``chunks`` and ``sources``.
        """
        return self.retriever.retrieve(question, top_k=top_k)

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def generate(
        self,
        question: str,
        context_chunks: List[str],
        chat_history: Optional[List[Dict]] = None,
    ) -> str:
        """
        Generate a complete answer (non-streaming).

        Args:
            question: User question.
            context_chunks: Retrieved document chunks.
            chat_history: Previous conversation messages.

        Returns:
            Full answer string.
        """
        messages = self._build_messages(question, context_chunks, chat_history)
        return invoke_llm(messages)

    def generate_stream(
        self,
        question: str,
        context_chunks: List[str],
        chat_history: Optional[List[Dict]] = None,
    ) -> Generator[str, None, None]:
        """
        Stream answer tokens.

        Args:
            question: User question.
            context_chunks: Retrieved document chunks.
            chat_history: Previous conversation messages.

        Yields:
            Individual tokens.
        """
        messages = self._build_messages(question, context_chunks, chat_history)
        yield from stream_llm_response(messages)

    # ------------------------------------------------------------------
    # Prompt building
    # ------------------------------------------------------------------

    def _build_messages(
        self,
        question: str,
        context_chunks: List[str],
        chat_history: Optional[List[Dict]] = None,
    ) -> List:
        """Construct the final prompt messages with system instructions, context, and history."""
        # Format context
        if context_chunks:
            context = "\n\n---\n\n".join(context_chunks)
        else:
            context = "No relevant documents found."

        # Format chat history
        history_str = ""
        if chat_history:
            for msg in chat_history[-10:]:  # Last 10 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                history_str += f"{role.upper()}: {content}\n"

        # Combine
        user_content = QA_PROMPT_TEMPLATE.format(
            context=context,
            chat_history=history_str or "No previous conversation.",
            question=question,
        )

        return [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_content)
        ]
