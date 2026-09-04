"""Token optimization: semantic-ish chunking plus near-duplicate removal.

Uses a ~4 chars/token heuristic (same as OKF pipeline). Does not send text
to external embedding APIs.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from app.agents.types import TokenOptimizationReport

CHARS_PER_TOKEN = 4
MIN_CHUNK_TOKENS = 500
MAX_CHUNK_TOKENS = 1000
COMPACT_CONTEXT_CHARS = 280
JACCARD_DEDUP = 0.92


def estimate_tokens(text: str) -> int:
    return max(1, (len(text) + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN) if text else 0


def compact_context(text: str, limit: int = COMPACT_CONTEXT_CHARS) -> str:
    collapsed = re.sub(r"\s+", " ", text.strip())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 1].rstrip() + "…"


def _normalize_paragraph(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _tokens(text: str) -> set[str]:
    return {part for part in re.findall(r"[a-z0-9]+", _normalize_paragraph(text)) if part}


def jaccard(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def dedupe_paragraphs(paragraphs: list[str], threshold: float = JACCARD_DEDUP) -> tuple[list[str], int]:
    kept: list[str] = []
    removed = 0
    for paragraph in paragraphs:
        body = paragraph.strip()
        if not body:
            continue
        if any(jaccard(body, existing) >= threshold for existing in kept):
            removed += 1
            continue
        kept.append(body)
    return kept, removed


def split_paragraphs(text: str) -> list[str]:
    parts = re.split(r"\n\s*\n+", text.strip())
    if len(parts) == 1:
        parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9§])", text.strip())
    return [part.strip() for part in parts if part.strip()]


def chunk_text(text: str) -> tuple[list[dict[str, Any]], int]:
    """Chunk toward 500–1000 tokens. Merge undersized siblings; split oversized."""
    paragraphs, removed = dedupe_paragraphs(split_paragraphs(text))
    chunks: list[dict[str, Any]] = []
    buffer: list[str] = []
    buffer_tokens = 0
    index = 0

    def flush() -> None:
        nonlocal buffer, buffer_tokens, index
        if not buffer:
            return
        body = "\n\n".join(buffer)
        tokens = estimate_tokens(body)
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
        chunks.append(
            {
                "chunkId": f"chk-{index:04d}-{digest}",
                "text": body,
                "tokenCount": tokens,
                "chunkIndex": index,
            }
        )
        index += 1
        buffer = []
        buffer_tokens = 0

    for paragraph in paragraphs:
        tokens = estimate_tokens(paragraph)
        if tokens > MAX_CHUNK_TOKENS:
            flush()
            words = paragraph.split()
            window: list[str] = []
            window_tokens = 0
            for word in words:
                word_tokens = estimate_tokens(word + " ")
                if window and window_tokens + word_tokens > MAX_CHUNK_TOKENS:
                    buffer = [" ".join(window)]
                    buffer_tokens = window_tokens
                    flush()
                    window = [word]
                    window_tokens = word_tokens
                else:
                    window.append(word)
                    window_tokens += word_tokens
            if window:
                buffer = [" ".join(window)]
                buffer_tokens = window_tokens
                flush()
            continue
        if buffer and buffer_tokens + tokens > MAX_CHUNK_TOKENS:
            flush()
        buffer.append(paragraph)
        buffer_tokens += tokens
        if buffer_tokens >= MIN_CHUNK_TOKENS:
            flush()
    flush()
    return chunks, removed


def optimize_tokens(text: str) -> tuple[str, list[dict[str, Any]], TokenOptimizationReport]:
    original = estimate_tokens(text)
    chunks, removed = chunk_text(text)
    optimized_body = "\n\n".join(chunk["text"] for chunk in chunks)
    report = TokenOptimizationReport(
        original_tokens=original,
        optimized_tokens=estimate_tokens(optimized_body),
        chunks=len(chunks),
        duplicates_removed=removed,
        compact_context_chars=len(compact_context(text)),
    )
    return optimized_body, chunks, report
