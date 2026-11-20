"""Small, dependency-free BM25 scoring for the local MARAS index."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9._-]{1,}", text.casefold())


def term_frequencies(text: str) -> dict[str, int]:
    return dict(Counter(tokenize(text)))


def bm25_scores(query: str, documents: list[dict[str, Any]]) -> dict[str, float]:
    """Score indexed chunks with BM25; scores are ranking signals, not confidence."""
    if not documents:
        return {}
    query_terms = set(tokenize(query))
    if not query_terms:
        return {}
    frequencies = [
        item.get("term_vector") if isinstance(item.get("term_vector"), dict)
        else term_frequencies(item.get("text", ""))
        for item in documents
    ]
    lengths = [sum(vector.values()) for vector in frequencies]
    average_length = sum(lengths) / max(len(lengths), 1)
    document_frequency = {
        term: sum(1 for vector in frequencies if vector.get(term, 0) > 0)
        for term in query_terms
    }
    scores: dict[str, float] = {}
    total = len(documents)
    k1 = 1.5
    b = 0.75
    for item, vector, length in zip(documents, frequencies, lengths, strict=True):
        score = 0.0
        for term in query_terms:
            frequency = vector.get(term, 0)
            if not frequency:
                continue
            df = document_frequency[term]
            inverse_frequency = math.log(
                1.0 + (total - df + 0.5) / (df + 0.5)
            )
            denominator = frequency + k1 * (
                1.0 - b + b * length / max(average_length, 1.0)
            )
            score += inverse_frequency * (
                frequency * (k1 + 1.0) / denominator
            )
        scores[item["chunk_id"]] = round(score, 8)
    return scores
