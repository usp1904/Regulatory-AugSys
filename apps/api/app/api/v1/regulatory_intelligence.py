"""Regulatory Intelligence endpoints backed by the modular RAG engine."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.requirements_mapping import require_mapping_reader, require_mapping_writer
from app.core.database import get_db
from app.schemas.regulatory_intelligence import (
    RegulatoryIndexRequest,
    RegulatoryIndexResponse,
    RegulatoryQueryResponse,
    RegulatoryRetrievalRequest,
    RegulatoryRetrievalResponse,
)
from app.services.regulatory_intelligence import (
    get_regulatory_candidate_graph,
    execute_regulatory_intelligence_query,
    index_regulatory_document,
    list_indexable_documents,
    retrieve_regulatory_evidence,
)

router = APIRouter(prefix="/regulatory-intelligence", tags=["regulatory-intelligence"])


@router.get("/documents")
def get_indexable_documents(
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_reader),
) -> list[dict]:
    return list_indexable_documents(db)


@router.post("/index", response_model=RegulatoryIndexResponse)
def index_document(
    payload: RegulatoryIndexRequest,
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_writer),
) -> RegulatoryIndexResponse:
    try:
        return index_regulatory_document(db, payload.document_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/graph/{document_id}")
def get_candidate_graph(
    document_id: int,
    _access: str = Depends(require_mapping_reader),
) -> dict:
    """Return bounded, provenance-linked candidate graph data for an indexed document."""
    from app.regulatory_rag.engine import _local_store

    graph = get_regulatory_candidate_graph(document_id)
    stats = _local_store().stats(document_id)
    if stats["chunk_count"] == 0:
        raise HTTPException(
            status_code=404,
            detail="Document has not been indexed in the local RAG engine.",
        )
    return {
        "document_id": document_id,
        "graph_semantics": "CANDIDATE_CO_MENTION_NOT_VALIDATED_REGULATORY_RELATIONSHIP",
        **graph,
    }


@router.post("/retrieve", response_model=RegulatoryRetrievalResponse)
def retrieve_evidence(
    payload: RegulatoryRetrievalRequest,
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_reader),
) -> RegulatoryRetrievalResponse:
    return retrieve_regulatory_evidence(db, payload)



@router.post("/query", response_model=RegulatoryQueryResponse)
def run_regulatory_query(
    payload: RegulatoryRetrievalRequest,
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_reader),
) -> dict:
    return execute_regulatory_intelligence_query(db, payload)
