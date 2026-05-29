"""
Document metadata model.
Tracks file metadata throughout the ingestion pipeline.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class DocumentMetadata:
    """Metadata attached to every ingested document."""
    filename: str
    file_type: str
    file_size: int  # bytes
    upload_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    chunk_count: int = 0
    status: str = "processing"  # processing | processed | failed
    error_message: Optional[str] = None
    file_path: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "upload_time": self.upload_time,
            "chunk_count": self.chunk_count,
            "status": self.status,
            "error_message": self.error_message,
        }
