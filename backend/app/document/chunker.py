"""
Clinexa — Text Chunker
Phase 2: Sliding-window chunking with approximate token counting.

Strategy:
- Split text into sentences / lines, then greedily pack into chunks of
  ~chunk_tokens each with an overlap of ~overlap_tokens.
- Token estimate: 1 token ≈ 4 characters (GPT/Llama average for English).
- Each chunk is returned as a plain string.
"""
from __future__ import annotations

import re
import logging
from typing import Optional

log = logging.getLogger(__name__)

# Approximate chars per token for English text
CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Approximate token count from character count."""
    return max(1, len(text) // CHARS_PER_TOKEN)


def _split_into_sentences(text: str) -> list[str]:
    """
    Split text into sentence-level units.
    Tries to respect newlines and sentence boundaries.
    """
    # Split on sentence-ending punctuation followed by whitespace, OR on newlines
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    # Filter empty strings
    return [p.strip() for p in parts if p.strip()]


def chunk_text(
    text: str,
    chunk_tokens: int = 500,
    overlap_tokens: int = 50,
    min_chunk_chars: int = 20,
) -> list[str]:
    """
    Chunk `text` into overlapping windows of approximately `chunk_tokens` tokens.

    Args:
        text: The input text to chunk.
        chunk_tokens: Target maximum tokens per chunk (~500 words).
        overlap_tokens: Tokens to repeat at the start of the next chunk for
                        context continuity (~50 tokens).
        min_chunk_chars: Chunks shorter than this are dropped (noise).

    Returns:
        List of text chunks.
    """
    if not text or not text.strip():
        return []

    chunk_chars = chunk_tokens * CHARS_PER_TOKEN
    overlap_chars = overlap_tokens * CHARS_PER_TOKEN

    sentences = _split_into_sentences(text)
    if not sentences:
        return []

    chunks: list[str] = []
    current_sentences: list[str] = []
    current_len = 0

    for sentence in sentences:
        s_len = len(sentence)

        # If this single sentence already exceeds chunk size, hard-split it
        if s_len > chunk_chars and not current_sentences:
            # Break the long sentence by characters
            for i in range(0, s_len, chunk_chars - overlap_chars):
                piece = sentence[i : i + chunk_chars].strip()
                if len(piece) >= min_chunk_chars:
                    chunks.append(piece)
            continue

        # Will adding this sentence overflow the chunk?
        if current_len + s_len > chunk_chars and current_sentences:
            chunk_text_val = " ".join(current_sentences).strip()
            if len(chunk_text_val) >= min_chunk_chars:
                chunks.append(chunk_text_val)

            # Roll back by `overlap_chars` worth of sentences
            overlap_buf: list[str] = []
            overlap_len = 0
            for prev in reversed(current_sentences):
                if overlap_len + len(prev) <= overlap_chars:
                    overlap_buf.insert(0, prev)
                    overlap_len += len(prev)
                else:
                    break

            current_sentences = overlap_buf
            current_len = overlap_len

        current_sentences.append(sentence)
        current_len += s_len

    # Flush the last chunk
    if current_sentences:
        chunk_text_val = " ".join(current_sentences).strip()
        if len(chunk_text_val) >= min_chunk_chars:
            chunks.append(chunk_text_val)

    log.debug(
        "chunker.done",
        input_chars=len(text),
        num_chunks=len(chunks),
        chunk_tokens=chunk_tokens,
        overlap_tokens=overlap_tokens,
    )
    return chunks
