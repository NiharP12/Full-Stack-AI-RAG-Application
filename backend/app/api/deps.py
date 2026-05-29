"""
Dependency injection helpers for API routes.
"""

from app.config import settings


def get_settings():
    """Return the application settings singleton."""
    return settings
