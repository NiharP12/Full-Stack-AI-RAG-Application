"""
Document management endpoints — list and delete ingested documents.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.models.schemas import DeleteResponse, DocumentInfo, DocumentListResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    """List all uploaded and processed documents."""
    from app.services.document_service import DocumentService

    doc_service = DocumentService()
    docs = doc_service.list_documents()

    doc_infos = [
        DocumentInfo(
            filename=d["filename"],
            file_type=d.get("file_type", "unknown"),
            file_size=d.get("file_size", 0),
            upload_time=d.get("upload_time", ""),
            chunk_count=d.get("chunk_count", 0),
            status=d.get("status", "unknown"),
        )
        for d in docs
    ]

    return DocumentListResponse(
        documents=doc_infos,
        total_count=len(doc_infos),
    )


@router.delete("/documents", response_model=DeleteResponse)
async def delete_documents(
    filename: Optional[str] = Query(None, description="Specific file to delete. Omit to delete all."),
):
    """
    Delete documents from the system.

    - If ``filename`` is provided, delete only that document.
    - If omitted, delete **all** documents and reset the vector store.
    """
    from app.services.document_service import DocumentService

    doc_service = DocumentService()

    try:
        if filename:
            deleted = doc_service.delete_document(filename)
            return DeleteResponse(message=f"Deleted {filename}", deleted_files=deleted)
        else:
            deleted = doc_service.delete_all_documents()
            return DeleteResponse(message="All documents deleted", deleted_files=deleted)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{filename}' not found",
        )
    except Exception as exc:
        logger.error("Delete error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete documents: {str(exc)}",
        )
