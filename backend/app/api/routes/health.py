"""
Health check endpoint.
"""

import time
import logging

from fastapi import APIRouter

from app.config import settings
from app.models.schemas import HealthResponse

router = APIRouter()
logger = logging.getLogger(__name__)

# Track server start time
_start_time = time.time()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns server status, LLM provider, vector store info, and uptime.
    """
    # Count documents in the metadata store
    doc_count = 0
    try:
        from app.services.document_service import DocumentService
        doc_service = DocumentService()
        doc_count = len(doc_service.list_documents())
    except Exception:
        pass

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        llm_provider=settings.llm_provider,
        vector_store=settings.vector_store_type,
        documents_count=doc_count,
        uptime_seconds=round(time.time() - _start_time, 2),
    )
