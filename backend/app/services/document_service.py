"""
Document service — orchestrates file processing and metadata tracking.
"""

import json
import logging
import os
import threading
from datetime import datetime
from typing import Dict, List, Optional

from app.config import settings
from app.models.document import DocumentMetadata
from app.services.file_processor import FileProcessor
from app.rag.pipeline import RAGPipeline

logger = logging.getLogger(__name__)

# Thread-safe metadata store
_documents_lock = threading.Lock()
_METADATA_FILE = os.path.join(settings.upload_dir, "documents_metadata.json")


class DocumentService:
    """Manages document lifecycle: upload tracking, processing, and deletion."""

    def __init__(self):
        self.processor = FileProcessor()
        self.pipeline = RAGPipeline()

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def process_document(self, file_path: str, filename: str) -> DocumentMetadata:
        """
        Process a single document through the RAG pipeline.

        1. Extract text from the file
        2. Chunk the text
        3. Generate embeddings and store in vector DB
        4. Update metadata

        Args:
            file_path: Path to the uploaded file.
            filename: Original filename.

        Returns:
            DocumentMetadata with processing status.
        """
        file_size = os.path.getsize(file_path)
        ext = os.path.splitext(filename)[1].lower()

        meta = DocumentMetadata(
            filename=filename,
            file_type=ext,
            file_size=file_size,
            file_path=file_path,
            status="processing",
        )

        # Save initial metadata
        self._save_metadata(meta)

        try:
            # Extract text
            result = self.processor.process(file_path)
            text = result.get("text", "")
            pages = result.get("pages", [])

            if not text.strip():
                raise ValueError("No text could be extracted from the file")

            # Ingest into vector store
            doc_metadata = {
                "source": filename,
                "file_type": ext,
            }

            if pages:
                chunk_count = self.pipeline.ingest_pages(pages, metadata=doc_metadata)
            else:
                chunk_count = self.pipeline.ingest(text, metadata=doc_metadata)

            # Update metadata
            meta.chunk_count = chunk_count
            meta.status = "processed"
            self._save_metadata(meta)

            logger.info("Document processed: %s (%d chunks)", filename, chunk_count)
            return meta

        except Exception as exc:
            meta.status = "failed"
            meta.error_message = str(exc)
            self._save_metadata(meta)
            logger.error("Document processing failed: %s — %s", filename, exc, exc_info=True)
            raise

    # ------------------------------------------------------------------
    # Metadata management
    # ------------------------------------------------------------------

    def list_documents(self) -> List[Dict]:
        """Return metadata for all tracked documents."""
        data = self._load_all_metadata()
        return list(data.values())

    def mark_failed(self, filename: str, error: str) -> None:
        """Mark a document as failed."""
        data = self._load_all_metadata()
        if filename in data:
            data[filename]["status"] = "failed"
            data[filename]["error_message"] = error
            self._write_all_metadata(data)

    def delete_document(self, filename: str) -> List[str]:
        """
        Delete a specific document and its vector embeddings.

        Returns:
            List of deleted filenames.
        """
        data = self._load_all_metadata()
        if filename not in data:
            raise FileNotFoundError(f"Document not found: {filename}")

        # Delete from vector store
        from app.rag.vectorstore import VectorStoreManager
        vs = VectorStoreManager()
        vs.load_or_create()
        vs.delete_by_source(filename)

        # Delete file from disk
        file_path = data[filename].get("file_path")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

        # Remove metadata
        del data[filename]
        self._write_all_metadata(data)

        logger.info("Deleted document: %s", filename)
        return [filename]

    def delete_all_documents(self) -> List[str]:
        """Delete all documents, embeddings, and uploaded files."""
        data = self._load_all_metadata()
        deleted = list(data.keys())

        # Clear vector store
        from app.rag.vectorstore import VectorStoreManager
        vs = VectorStoreManager()
        vs.delete_all()

        # Delete uploaded files
        for doc_info in data.values():
            file_path = doc_info.get("file_path")
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

        # Clear metadata
        self._write_all_metadata({})

        logger.info("Deleted all %d documents", len(deleted))
        return deleted

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _save_metadata(self, meta: DocumentMetadata) -> None:
        """Save or update a single document's metadata."""
        with _documents_lock:
            data = self._load_all_metadata()
            entry = meta.to_dict()
            entry["file_path"] = meta.file_path
            data[meta.filename] = entry
            self._write_all_metadata(data)

    def _load_all_metadata(self) -> Dict:
        """Load metadata from the JSON file."""
        if not os.path.exists(_METADATA_FILE):
            return {}
        try:
            with open(_METADATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _write_all_metadata(self, data: Dict) -> None:
        """Write metadata to the JSON file."""
        os.makedirs(os.path.dirname(_METADATA_FILE), exist_ok=True)
        with open(_METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
