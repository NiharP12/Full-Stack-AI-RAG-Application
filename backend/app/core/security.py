"""
Security utilities — authentication scaffolding.
Provides API-key-based auth middleware ready for extension to JWT/OAuth.
"""

import logging
from typing import Optional

from fastapi import Header, HTTPException, status

from app.config import settings

logger = logging.getLogger(__name__)


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> Optional[str]:
    """
    Optional API key verification dependency.

    If an API key is configured in the environment, requests must include
    a matching ``X-API-Key`` header.  When no key is configured the
    dependency is a no-op so local development works without friction.

    Returns:
        The validated API key, or None when auth is disabled.
    """
    configured_key = getattr(settings, "api_key", None) or ""
    if not configured_key:
        # Auth not configured — allow all requests
        return None

    if not x_api_key or x_api_key != configured_key:
        logger.warning("Rejected request with invalid API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return x_api_key


def sanitize_input(text: str) -> str:
    """
    Basic input sanitisation to prevent prompt-injection / XSS.

    Strips control characters and limits length.
    """
    if not text:
        return ""
    # Remove null bytes and other control characters
    cleaned = "".join(ch for ch in text if ch == "\n" or ch == "\t" or (ord(ch) >= 32))
    # Limit to 10 000 characters for chat queries
    return cleaned[:10_000]
