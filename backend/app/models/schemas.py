"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    """Incoming chat question."""
    question: str = Field(..., min_length=1, max_length=10000, description="User question")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    top_k: Optional[int] = Field(None, ge=1, le=20, description="Override default top-k retrieval count")


class SourceDocument(BaseModel):
    """A source chunk referenced in the answer."""
    content: str = Field(..., description="Text snippet from the source")
    source: str = Field(..., description="Original file name")
    page: Optional[int] = Field(None, description="Page number (if applicable)")
    score: Optional[float] = Field(None, description="Similarity score")


class ChatResponse(BaseModel):
    """Chat answer with source citations."""
    answer: str
    sources: List[SourceDocument] = []
    session_id: str
    tokens_used: Optional[int] = None


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

class UploadResponse(BaseModel):
    """Response after uploading files."""
    message: str
    uploaded_files: List[str]
    failed_files: List[Dict[str, str]] = []
    total_chunks: int = 0


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

class DocumentInfo(BaseModel):
    """Metadata about an ingested document."""
    filename: str
    file_type: str
    file_size: int  # bytes
    upload_time: str
    chunk_count: int
    status: str  # "processed", "processing", "failed"


class DocumentListResponse(BaseModel):
    """List of all ingested documents."""
    documents: List[DocumentInfo]
    total_count: int


class DeleteResponse(BaseModel):
    """Response after deleting documents."""
    message: str
    deleted_files: List[str]


# ---------------------------------------------------------------------------
# Chat History
# ---------------------------------------------------------------------------

class HistoryMessage(BaseModel):
    """A single message in the chat history."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    sources: Optional[List[SourceDocument]] = None


class ChatSession(BaseModel):
    """A chat session with its messages."""
    session_id: str
    title: str
    created_at: str
    updated_at: str
    messages: List[HistoryMessage] = []


class HistoryResponse(BaseModel):
    """Chat history response."""
    sessions: List[ChatSession]


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    llm_provider: str
    vector_store: str
    documents_count: int
    uptime_seconds: float
