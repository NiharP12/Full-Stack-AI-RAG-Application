"""
Chat service — manages conversation history and session persistence.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from app.config import settings
from app.models.schemas import ChatSession, HistoryMessage, SourceDocument

logger = logging.getLogger(__name__)


class ChatService:
    """Manages chat sessions and conversation memory."""

    def __init__(self):
        self.history_dir = settings.chat_history_dir
        os.makedirs(self.history_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Session file helpers
    # ------------------------------------------------------------------

    def _session_path(self, session_id: str) -> str:
        """Return the file path for a session."""
        safe_id = "".join(c for c in session_id if c.isalnum() or c in "-_")
        return os.path.join(self.history_dir, f"{safe_id}.json")

    def _load_session(self, session_id: str) -> Dict:
        """Load a session from disk."""
        path = self._session_path(session_id)
        if not os.path.exists(path):
            return {
                "session_id": session_id,
                "title": "New Chat",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "messages": [],
            }
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {
                "session_id": session_id,
                "title": "New Chat",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "messages": [],
            }

    def _save_session(self, session_id: str, data: Dict) -> None:
        """Persist a session to disk."""
        path = self._session_path(session_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[List[SourceDocument]] = None,
    ) -> None:
        """
        Save a message to a session's history.

        Args:
            session_id: Session identifier.
            role: "user" or "assistant".
            content: Message text.
            sources: Optional source citations (for assistant messages).
        """
        session = self._load_session(session_id)

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if sources:
            message["sources"] = [s.dict() if hasattr(s, "dict") else s for s in sources]

        session["messages"].append(message)
        session["updated_at"] = datetime.utcnow().isoformat()

        # Auto-title from first user message
        if session["title"] == "New Chat" and role == "user":
            session["title"] = content[:60] + ("..." if len(content) > 60 else "")

        self._save_session(session_id, session)

    def get_conversation_memory(
        self,
        session_id: str,
        max_messages: Optional[int] = None,
    ) -> List[Dict]:
        """
        Get recent conversation messages for context.

        Args:
            session_id: Session identifier.
            max_messages: Max messages to return (default from settings).

        Returns:
            List of message dicts with role and content.
        """
        limit = max_messages or settings.max_conversation_memory
        session = self._load_session(session_id)
        messages = session.get("messages", [])

        # Return the last N messages
        return [
            {"role": m["role"], "content": m["content"]}
            for m in messages[-limit:]
        ]

    def get_history(self, session_id: Optional[str] = None) -> List[ChatSession]:
        """
        Get chat history.

        Args:
            session_id: If provided, return only that session.
                        Otherwise return all sessions.

        Returns:
            List of ChatSession objects.
        """
        if session_id:
            data = self._load_session(session_id)
            return [self._dict_to_session(data)]

        # List all sessions
        sessions = []
        if not os.path.exists(self.history_dir):
            return sessions

        for filename in os.listdir(self.history_dir):
            if filename.endswith(".json"):
                path = os.path.join(self.history_dir, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    sessions.append(self._dict_to_session(data))
                except Exception:
                    continue

        # Sort by updated_at descending
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions

    def delete_session(self, session_id: str) -> None:
        """Delete a single session."""
        path = self._session_path(session_id)
        if os.path.exists(path):
            os.remove(path)
            logger.info("Deleted chat session: %s", session_id)

    def delete_all_history(self) -> None:
        """Delete all chat history."""
        if os.path.exists(self.history_dir):
            for filename in os.listdir(self.history_dir):
                if filename.endswith(".json"):
                    os.remove(os.path.join(self.history_dir, filename))
            logger.info("Deleted all chat history")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _dict_to_session(self, data: Dict) -> ChatSession:
        """Convert a raw dict to a ChatSession model."""
        messages = []
        for m in data.get("messages", []):
            sources = None
            if m.get("sources"):
                sources = [
                    SourceDocument(**s) if isinstance(s, dict) else s
                    for s in m["sources"]
                ]
            messages.append(
                HistoryMessage(
                    role=m["role"],
                    content=m["content"],
                    timestamp=m.get("timestamp", ""),
                    sources=sources,
                )
            )

        return ChatSession(
            session_id=data.get("session_id", ""),
            title=data.get("title", "Untitled"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            messages=messages,
        )
