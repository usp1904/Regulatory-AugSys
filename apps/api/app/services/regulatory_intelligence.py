"""MARAS Regulatory Intelligence API orchestration and compatibility layer."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.regulatory_rag.engine import index_document, retrieve_hybrid
from app.schemas.regulatory_intelligence import (
    RegulatoryEvidenceItem,
    RegulatoryIndexResponse,
    RegulatoryRetrievalRequest,
    RegulatoryRetrievalResponse,
)


def retrieve_regulatory_evidence(
    db: Session,
    payload: RegulatoryRetrievalRequest,
) -> RegulatoryRetrievalResponse:
    result = retrieve_hybrid(db, payload.query, payload.document_ids, payload.top_k)
    items = [
        RegulatoryEvidenceItem(
            document_id=item["document_id"],
            filename=item["filename"],
            document_version=item["document_version"],
            file_hash=item["file_hash"],
            chunk_id=item["chunk_id"],
            source_status=item["source_status"],
            location_type=item["location_type"],
            location=item["location"],
            excerpt=item["excerpt"],
            score=item["fusion_score"],
        )
        for item in result["results"]
    ]
    return RegulatoryRetrievalResponse(
        status=result["status"],
        query=result["query"],
        results=items,
        message=f"{result['message']} Retrieval mode: {result['retrieval_mode']}.",
    )


def index_regulatory_document(db: Session, document_id: int) -> RegulatoryIndexResponse:
    result = index_document(db, document_id)
    return RegulatoryIndexResponse(**{
        key: result[key] for key in RegulatoryIndexResponse.model_fields
    })


def list_indexable_documents(db: Session) -> list[dict]:
    documents = db.scalars(
        select(Document)
        .where(Document.parse_status == "EXTRACTED")
        .order_by(Document.id.desc())
    ).all()
    return [
        {
            "document_id": item.id,
            "filename": item.filename,
            "version": item.version,
            "file_hash": item.file_hash,
            "parse_status": item.parse_status,
        }
        for item in documents
    ]



def execute_regulatory_intelligence_query(
    db: Session,
    payload: RegulatoryRetrievalRequest,
) -> dict:
    """Execute the bounded planner and hybrid retrieval flow with an inspectable trace."""
    from app.regulatory_rag.orchestrator import execute_regulatory_query

    result = execute_regulatory_query(
        db, payload.query, payload.document_ids, payload.top_k
    )
    result["results"] = [
        {
            **item,
            "score": item["fusion_score"],
        }
        for item in result["results"]
    ]
    return result


def get_regulatory_candidate_graph(document_id: int) -> dict:
    """Read the persisted source-linked candidate graph for one indexed document."""
    from app.regulatory_rag.engine import _local_store

    return _local_store().graph_for_document(document_id)
