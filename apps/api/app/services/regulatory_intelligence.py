"""Deterministic evidence retrieval over existing MARAS document records.

This is the first integration slice, not production Graph RAG. It deliberately
returns source excerpts rather than generating an answer without validated
embedding, graph and model providers.
"""

from __future__ import annotations

import re
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.schemas.regulatory_intelligence import (
    RegulatoryEvidenceItem,
    RegulatoryRetrievalRequest,
    RegulatoryRetrievalResponse,
)

_TOKEN_RE = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9._-]{1,}")
_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "how", "in", "is", "it", "of", "on", "or", "that", "the", "to",
    "under", "what", "when", "where", "which", "with",
}


def _tokens(value: str) -> list[str]:
    return [
        token.casefold()
        for token in _TOKEN_RE.findall(value)
        if token.casefold() not in _STOP_WORDS
    ]


def _score(query_terms: list[str], text: str) -> float:
    """Return a bounded token-coverage score; not a semantic similarity score."""
    if not query_terms:
        return 0.0
    counts = Counter(_tokens(text))
    unique_terms = set(query_terms)
    matched = sum(1 for term in unique_terms if counts.get(term, 0))
    coverage = matched / len(unique_terms)
    frequency = sum(min(counts.get(term, 0), 3) for term in unique_terms)
    frequency_bonus = min(frequency / (len(unique_terms) * 3), 1.0) * 0.15
    return round(min(coverage + frequency_bonus, 1.0), 4)


def retrieve_regulatory_evidence(
    db: Session,
    payload: RegulatoryRetrievalRequest,
) -> RegulatoryRetrievalResponse:
    """Search extracted page/paragraph text and return versioned source evidence."""
    query_terms = _tokens(payload.query)
    if not query_terms:
        return RegulatoryRetrievalResponse(
            status="NO_MATCH",
            query=payload.query,
            results=[],
            message="The query did not contain searchable terms.",
        )

    statement = (
        select(Document)
        .where(Document.parse_status == "EXTRACTED")
        .order_by(Document.id.desc())
    )
    if payload.document_ids:
        statement = statement.where(Document.id.in_(payload.document_ids))

    documents = db.scalars(statement).all()
    results: list[RegulatoryEvidenceItem] = []

    for document in documents:
        if document.pages:
            passages = [
                (f"page:{page.page_number}", page.text_content)
                for page in document.pages
            ]
        elif document.paragraphs:
            passages = [
                (f"paragraph:{paragraph.paragraph_index}", paragraph.text_content)
                for paragraph in document.paragraphs
            ]
        else:
            passages = [("document:excerpt", document.text_excerpt or "")]

        for location, passage in passages:
            if not passage.strip():
                continue
            score = _score(query_terms, passage)
            if score <= 0:
                continue
            excerpt = re.sub(r"\s+", " ", passage).strip()
            if len(excerpt) > 1200:
                excerpt = excerpt[:1197].rstrip() + "..."
            results.append(
                RegulatoryEvidenceItem(
                    document_id=document.id,
                    filename=document.filename,
                    document_version=document.version,
                    file_hash=document.file_hash,
                    location_type=location.split(":", maxsplit=1)[0],
                    location=location,
                    excerpt=excerpt,
                    score=score,
                )
            )

    results.sort(key=lambda item: (item.score, item.document_id), reverse=True)
    selected = results[: payload.top_k]
    return RegulatoryRetrievalResponse(
        status="OK" if selected else "NO_MATCH",
        query=payload.query,
        results=selected,
        message=(
            "Evidence retrieved from existing MARAS documents. Scores are lexical "
            "coverage heuristics, not embedding similarity or confidence."
            if selected
            else "No matching extracted passages were found in the selected document scope."
        ),
    )
