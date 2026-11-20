"""Structure-aware chunking for existing MARAS extracted document records."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from app.models.document import Document


@dataclass(frozen=True)
class RegulatoryChunk:
    chunk_id: str
    document_id: int
    document_version: int
    file_hash: str
    filename: str
    page_number: int | None
    ordinal: int
    heading: str
    text: str


def _split_text(text: str, max_chars: int, overlap: int) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + max_chars, len(normalized))
        if end < len(normalized):
            boundary = max(
                normalized.rfind(". ", start + max_chars // 2, end),
                normalized.rfind("; ", start + max_chars // 2, end),
            )
            if boundary > start:
                end = boundary + 1
        value = normalized[start:end].strip()
        if value:
            chunks.append(value)
        if end >= len(normalized):
            break
        start = max(end - overlap, start + 1)
    return chunks


def build_document_chunks(
    document: Document, *, max_chars: int = 1400, overlap: int = 180
) -> list[RegulatoryChunk]:
    """Create stable, source-addressable chunks without duplicating MARAS documents."""
    source_pages = (
        [(page.page_number, page.text_content) for page in document.pages]
        if document.pages
        else [(None, paragraph.text_content) for paragraph in document.paragraphs]
        if document.paragraphs
        else [(None, document.text_excerpt or "")]
    )
    chunks: list[RegulatoryChunk] = []
    ordinal = 0
    for page_number, page_text in source_pages:
        heading_match = re.search(
            r"(?m)^\s*(?:\d+(?:\.\d+)*\s+)?([A-Z][^\n]{4,120})$", page_text
        )
        heading = heading_match.group(1).strip() if heading_match else ""
        for piece in _split_text(page_text, max_chars, overlap):
            ordinal += 1
            stable = (
                f"{document.id}:{document.version}:{document.file_hash}:"
                f"{page_number}:{ordinal}"
            )
            chunks.append(
                RegulatoryChunk(
                    chunk_id=hashlib.sha256(stable.encode()).hexdigest(),
                    document_id=document.id,
                    document_version=document.version,
                    file_hash=document.file_hash,
                    filename=document.filename,
                    page_number=page_number,
                    ordinal=ordinal,
                    heading=heading,
                    text=piece,
                )
            )
    return chunks
