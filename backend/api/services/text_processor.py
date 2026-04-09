"""
Text cleaning and chunking service.

Provides utilities for normalizing raw text and splitting it into
manageable chunks for the map-reduce summarization pipeline.
"""
import re
import logging

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """
    Normalize and clean raw extracted text.

    - Strips control characters (except newlines/tabs)
    - Collapses excessive whitespace
    - Removes non-printable characters

    Args:
        text: Raw text string.

    Returns:
        Cleaned text string.
    """
    # Remove control characters except \n and \t
    text = re.sub(r"[^\S\n\t]+", " ", text)
    # Collapse multiple blank lines into a single one
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(lines)
    # Final strip
    text = text.strip()

    return text


def chunk_text(text: str, chunk_size: int = 1500) -> list[str]:
    """
    Split text into chunks of approximately `chunk_size` words.

    Splits on word boundaries to avoid cutting mid-word.
    Each chunk is a contiguous block of text.

    Args:
        text:       The input text to chunk.
        chunk_size: Target number of words per chunk (default 1500).

    Returns:
        List of text chunks.
    """
    words = text.split()
    total_words = len(words)

    if total_words == 0:
        return []

    if total_words <= chunk_size:
        logger.info("Text fits in a single chunk (%d words).", total_words)
        return [text]

    chunks = []
    for start in range(0, total_words, chunk_size):
        chunk_words = words[start : start + chunk_size]
        chunks.append(" ".join(chunk_words))

    logger.info(
        "Split %d words into %d chunks (~%d words each).",
        total_words,
        len(chunks),
        chunk_size,
    )
    return chunks
