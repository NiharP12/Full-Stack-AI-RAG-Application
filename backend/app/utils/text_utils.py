"""
Text utility functions — cleaning and sanitisation.
"""

import re
import unicodedata


def clean_text(text: str) -> str:
    """
    Clean extracted text for better embedding quality.

    - Normalise unicode
    - Remove excessive whitespace
    - Remove null bytes
    - Normalise line endings
    """
    if not text:
        return ""

    # Unicode normalisation
    text = unicodedata.normalize("NFKC", text)

    # Remove null bytes
    text = text.replace("\x00", "")

    # Normalise line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse multiple blank lines into two
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse multiple spaces (but not newlines)
    text = re.sub(r"[^\S\n]+", " ", text)

    # Strip leading/trailing whitespace on each line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    return text.strip()


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to a maximum length, adding ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(" ", 1)[0] + "…"
