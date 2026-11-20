"""Extractive evidence synthesis with claim-to-source validation."""

from __future__ import annotations

import re
from typing import Any

from app.regulatory_rag.sparse import tokenize


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def _sentences(text: str) -> list[str]:
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", text)
        if sentence.strip()
    ]


def build_evidence_answer(query: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    """Select verbatim source sentences and validate each against its source excerpt."""
    query_terms = set(tokenize(query))
    candidates: list[tuple[float, str, dict[str, Any]]] = []
    for item in results:
        for sentence in _sentences(item.get("excerpt", "")):
            sentence_terms = set(tokenize(sentence))
            overlap = len(query_terms & sentence_terms)
            if overlap == 0 or len(sentence) < 24:
                continue
            score = overlap / max(len(query_terms), 1)
            candidates.append((score, sentence, item))

    candidates.sort(key=lambda entry: entry[0], reverse=True)
    claims: list[dict[str, Any]] = []
    seen: set[str] = set()
    for _, sentence, item in candidates:
        normalized = _normalize(sentence)
        if normalized in seen:
            continue
        # Exact normalized substring validation prevents unsupported paraphrases.
        if normalized not in _normalize(item.get("excerpt", "")):
            continue
        seen.add(normalized)
        claims.append(
            {
                "text": sentence,
                "citations": [
                    {
                        "document_id": item["document_id"],
                        "filename": item["filename"],
                        "document_version": item["document_version"],
                        "file_hash": item["file_hash"],
                        "location": item["location"],
                        "chunk_id": item["chunk_id"],
                    }
                ],
            }
        )
        if len(claims) >= 5:
            break

    answer_text = (
        " ".join(claim["text"] for claim in claims)
        if claims
        else "No source sentence could be safely selected for this question. Review the retrieved evidence or broaden the document scope."
    )
    return {
        "answer_mode": "EXTRACTIVE_EVIDENCE_ONLY",
        "answer_text": answer_text,
        "claims": claims,
        "validation_status": "PASSED" if claims else "ABSTAINED",
        "disclaimer": (
            "Statements are quoted from retrieved source passages. This is not a legal "
            "interpretation, applicability decision or compliance determination."
        ),
    }
