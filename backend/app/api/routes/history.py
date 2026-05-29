"""
Chat history endpoints — retrieve past conversations.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Query

from app.models.schemas import HistoryResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
):
    """
    Retrieve chat history.

    - If ``session_id`` is provided, returns messages for that session only.
    - Otherwise returns all sessions (summary view).
    """
    from app.services.chat_service import ChatService

    chat_service = ChatService()
    sessions = chat_service.get_history(session_id=session_id)

    return HistoryResponse(sessions=sessions)


@router.delete("/history")
async def delete_history(
    session_id: Optional[str] = Query(None, description="Session to delete. Omit to clear all."),
):
    """Delete chat history for a session or all sessions."""
    from app.services.chat_service import ChatService

    chat_service = ChatService()

    if session_id:
        chat_service.delete_session(session_id)
        return {"message": f"Session {session_id} deleted"}
    else:
        chat_service.delete_all_history()
        return {"message": "All chat history deleted"}
