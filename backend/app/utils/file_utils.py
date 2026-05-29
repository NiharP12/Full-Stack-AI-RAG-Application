"""
File utility functions — validation and cleanup.
"""

import os
from typing import List

from app.config import settings


def validate_file_extension(filename: str) -> bool:
    """Check if file extension is allowed."""
    ext = os.path.splitext(filename)[1].lower()
    return ext in settings.allowed_extensions_list


def validate_file_size(size_bytes: int) -> bool:
    """Check if file size is within the limit."""
    return size_bytes <= settings.max_file_size_bytes


def get_file_extension(filename: str) -> str:
    """Get the lowercase file extension."""
    return os.path.splitext(filename)[1].lower()


def cleanup_upload_dir() -> int:
    """
    Remove empty subdirectories in the upload directory.
    Returns number of directories removed.
    """
    removed = 0
    upload_dir = settings.upload_dir
    if not os.path.exists(upload_dir):
        return 0

    for entry in os.listdir(upload_dir):
        path = os.path.join(upload_dir, entry)
        if os.path.isdir(path):
            try:
                if not os.listdir(path):
                    os.rmdir(path)
                    removed += 1
            except OSError:
                pass

    return removed
