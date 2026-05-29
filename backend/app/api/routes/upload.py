"""
File upload endpoint — handles multi-file upload with validation and async processing.
"""

import logging
import os
import uuid
from typing import List

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile, status

from app.config import settings
from app.models.schemas import UploadResponse

router = APIRouter()
logger = logging.getLogger(__name__)


def _validate_file(file: UploadFile) -> None:
    """Validate file extension and size."""
    if not file.filename:
        raise ValueError("File has no name")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.allowed_extensions_list:
        raise ValueError(
            f"File type '{ext}' is not allowed. Supported: {settings.allowed_extensions_list}"
        )


async def _save_file(file: UploadFile) -> str:
    """Save uploaded file to disk and return the path."""
    # Generate a unique subdirectory to avoid name collisions
    unique_dir = os.path.join(settings.upload_dir, uuid.uuid4().hex[:8])
    os.makedirs(unique_dir, exist_ok=True)

    file_path = os.path.join(unique_dir, file.filename)

    content = await file.read()

    # Check file size
    if len(content) > settings.max_file_size_bytes:
        raise ValueError(
            f"File size ({len(content) / 1024 / 1024:.1f} MB) exceeds maximum ({settings.max_file_size_mb} MB)"
        )

    with open(file_path, "wb") as f:
        f.write(content)

    return file_path


def _process_files_background(file_paths: List[str], filenames: List[str]) -> None:
    """Background task: process uploaded files through the RAG pipeline."""
    from app.services.document_service import DocumentService

    doc_service = DocumentService()
    for path, name in zip(file_paths, filenames):
        try:
            doc_service.process_document(path, name)
            logger.info("Successfully processed: %s", name)
        except Exception as exc:
            logger.error("Failed to process %s: %s", name, exc, exc_info=True)
            doc_service.mark_failed(name, str(exc))


@router.post("/upload", response_model=UploadResponse)
async def upload_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(..., description="Files to upload (PDF, TXT, DOCX, CSV, XLSX)"),
):
    """
    Upload one or more files for RAG processing.

    Files are validated, saved to disk, then processed asynchronously
    (text extraction → chunking → embedding → vector store).
    """
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided")

    uploaded: List[str] = []
    failed: List[dict] = []
    file_paths: List[str] = []

    for file in files:
        try:
            _validate_file(file)
            path = await _save_file(file)
            file_paths.append(path)
            uploaded.append(file.filename)
            logger.info("Uploaded: %s → %s", file.filename, path)
        except ValueError as exc:
            failed.append({"filename": file.filename or "unknown", "error": str(exc)})
            logger.warning("Upload rejected: %s — %s", file.filename, exc)
        except Exception as exc:
            failed.append({"filename": file.filename or "unknown", "error": "Upload failed"})
            logger.error("Upload error for %s: %s", file.filename, exc, exc_info=True)

    # Schedule background processing
    if file_paths:
        background_tasks.add_task(_process_files_background, file_paths, uploaded)

    return UploadResponse(
        message=f"Uploaded {len(uploaded)} file(s). Processing in background.",
        uploaded_files=uploaded,
        failed_files=failed,
    )
