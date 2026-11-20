"""Deterministic intent classification and bounded retrieval planning."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalPlan:
    intent: str
    strategy: tuple[str, ...]
    clause_reference: str | None
    max_graph_hops: int
    rationale: str


_CLAUSE_RE = re.compile(
    r"\b(?:21\s*CFR\s*(?:Part\s*)?\d+(?:\.\d+)?|ICH\s*Q\d+[A-Z]?|"
    r"Annex\s*\d+|section\s+\d+(?:\.\d+)*)\b",
    re.I,
)


def plan_regulatory_query(query: str) -> RetrievalPlan:
    normalized = query.casefold()
    clause = _CLAUSE_RE.search(query)
    relationship_terms = ("related", "relationship", "linked", "impact", "affect", "depends on")
    obligation_terms = ("obligation", "shall", "must", "required", "requirement", "compliance")
    if clause:
        return RetrievalPlan(
            intent="CLAUSE_LOOKUP",
            strategy=("bm25", "optional_vector", "graph"),
            clause_reference=clause.group(0),
            max_graph_hops=1,
            rationale="A named regulation or clause reference was detected.",
        )
    if any(term in normalized for term in relationship_terms):
        return RetrievalPlan(
            intent="RELATIONSHIP_ANALYSIS",
            strategy=("bm25", "optional_vector", "graph"),
            clause_reference=None,
            max_graph_hops=1,
            rationale="The query asks how regulatory concepts or controls are connected.",
        )
    if any(term in normalized for term in obligation_terms):
        return RetrievalPlan(
            intent="OBLIGATION_RETRIEVAL",
            strategy=("bm25", "optional_vector", "graph"),
            clause_reference=None,
            max_graph_hops=1,
            rationale="The query focuses on obligations, requirements or compliance duties.",
        )
    return RetrievalPlan(
        intent="GENERAL_REGULATORY_RETRIEVAL",
        strategy=("bm25", "optional_vector", "graph"),
        clause_reference=None,
        max_graph_hops=1,
        rationale="Default grounded retrieval plan.",
    )
