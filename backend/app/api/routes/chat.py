"""
Chat endpoint — streaming RAG responses via Server-Sent Events.
"""

import json
import logging
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.config import settings
from app.core.security import sanitize_input
from app.models.schemas import ChatRequest, ChatResponse, SourceDocument

router = APIRouter()
logger = logging.getLogger(__name__)


async def _stream_response(question: str, session_id: str, top_k: int) -> AsyncGenerator[str, None]:
    """
    Generate SSE stream for a chat question.

    Yields ``data: {...}\\n\\n`` events:
    - ``{"type": "token", "content": "..."}`` — incremental answer tokens
    - ``{"type": "sources", "sources": [...]}`` — source citations
    - ``{"type": "done", "session_id": "..."}`` — end marker
    - ``{"type": "error", "content": "..."}`` — on failure
    """
    from app.services.chat_service import ChatService

    chat_service = ChatService()

    try:
        # Retrieve relevant context
        from app.rag.pipeline import RAGPipeline
        pipeline = RAGPipeline()

        retrieval_result = pipeline.retrieve(question, top_k=top_k)
        context_chunks = retrieval_result["chunks"]
        sources = retrieval_result["sources"]

        # Build source documents for the response
        source_docs = []
        for src in sources:
            source_docs.append(
                SourceDocument(
                    content=src.get("content", "")[:300],
                    source=src.get("source", "unknown"),
                    page=src.get("page"),
                    score=src.get("score"),
                )
            )

        # Get conversation history for context
        history = chat_service.get_conversation_memory(session_id)

        # Stream LLM response
        full_answer = ""
        try:
            for token in pipeline.generate_stream(
                question=question,
                context_chunks=context_chunks,
                chat_history=history,
            ):
                full_answer += token
                event_data = json.dumps({"type": "token", "content": token})
                yield f"data: {event_data}\n\n"
        except Exception as llm_exc:
            logger.error("LLM streaming error: %s", llm_exc, exc_info=True)
            # Fallback to non-streaming
            full_answer = pipeline.generate(
                question=question,
                context_chunks=context_chunks,
                chat_history=history,
            )
            event_data = json.dumps({"type": "token", "content": full_answer})
            yield f"data: {event_data}\n\n"

        # Send sources
        sources_data = json.dumps({
            "type": "sources",
            "sources": [s.dict() for s in source_docs],
        })
        yield f"data: {sources_data}\n\n"

        # Save to chat history
        chat_service.save_message(session_id, "user", question)
        chat_service.save_message(session_id, "assistant", full_answer, source_docs)

        # Done event
        done_data = json.dumps({"type": "done", "session_id": session_id})
        yield f"data: {done_data}\n\n"

    except Exception as exc:
        logger.error("Chat stream error: %s", exc, exc_info=True)
        error_data = json.dumps({"type": "error", "content": str(exc)})
        yield f"data: {error_data}\n\n"


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat with uploaded documents using RAG.

    Returns a streaming SSE response with incremental tokens,
    source citations, and a session ID.
    """
    question = sanitize_input(request.question)
    if not question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty",
        )

    session_id = request.session_id or str(uuid.uuid4())
    top_k = request.top_k or settings.top_k_results

    return StreamingResponse(
        _stream_response(question, session_id, top_k),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat/sync", response_model=ChatResponse)
async def chat_sync(request: ChatRequest):
    """
    Non-streaming chat endpoint — returns the full response at once.
    Useful for testing or clients that don't support SSE.
    """
    from app.services.chat_service import ChatService
    from app.rag.pipeline import RAGPipeline

    question = sanitize_input(request.question)
    if not question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty",
        )

    session_id = request.session_id or str(uuid.uuid4())
    top_k = request.top_k or settings.top_k_results

    pipeline = RAGPipeline()
    chat_service = ChatService()

    try:
        # Retrieve
        retrieval_result = pipeline.retrieve(question, top_k=top_k)
        context_chunks = retrieval_result["chunks"]
        sources = retrieval_result["sources"]

        # History
        history = chat_service.get_conversation_memory(session_id)

        # Generate
        answer = pipeline.generate(
            question=question,
            context_chunks=context_chunks,
            chat_history=history,
        )

        # Build sources
        source_docs = [
            SourceDocument(
                content=src.get("content", "")[:300],
                source=src.get("source", "unknown"),
                page=src.get("page"),
                score=src.get("score"),
            )
            for src in sources
        ]

        # Save history
        chat_service.save_message(session_id, "user", question)
        chat_service.save_message(session_id, "assistant", answer, source_docs)

        return ChatResponse(
            answer=answer,
            sources=source_docs,
            session_id=session_id,
        )

    except Exception as exc:
        logger.error("Chat error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate response: {str(exc)}",
        )
