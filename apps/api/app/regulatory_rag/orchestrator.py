"""Bounded orchestration of regulatory retrieval specialists."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.regulatory_rag.engine import retrieve_hybrid
from app.regulatory_rag.planner import plan_regulatory_query


def execute_regulatory_query(
    db: Session,
    query: str,
    document_ids: list[int] | None,
    top_k: int,
) -> dict:
    """Plan and execute retrieval; returns evidence and an inspectable execution trace."""
    plan = plan_regulatory_query(query)
    retrieval = retrieve_hybrid(db, query, document_ids, top_k)
    return {
        **retrieval,
        "plan": {
            "intent": plan.intent,
            "strategy": list(plan.strategy),
            "clause_reference": plan.clause_reference,
            "max_graph_hops": plan.max_graph_hops,
            "rationale": plan.rationale,
        },
        "trace": [
            {"stage": "intent_planning", "status": "completed"},
            {"stage": "lexical_retrieval", "status": "completed"},
            {
                "stage": "vector_retrieval",
                "status": "completed" if "VERTEX" in retrieval["retrieval_mode"] else "skipped",
            },
            {
                "stage": "graph_expansion",
                "status": "completed" if "GRAPH" in retrieval["retrieval_mode"] else "local_candidate_expansion",
            },
            {"stage": "evidence_assembly", "status": "completed"},
        ],
        "generation_status": "NOT_ENABLED_EVIDENCE_ONLY",
    }
