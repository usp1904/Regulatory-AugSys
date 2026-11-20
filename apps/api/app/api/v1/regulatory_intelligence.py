"""Regulatory Intelligence API: source-grounded retrieval slice."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.requirements_mapping import require_mapping_reader
from app.core.database import get_db
from app.schemas.regulatory_intelligence import (
    RegulatoryRetrievalRequest,
    RegulatoryRetrievalResponse,
)
from app.services.regulatory_intelligence import retrieve_regulatory_evidence

router = APIRouter(prefix="/regulatory-intelligence", tags=["regulatory-intelligence"])


@router.post("/retrieve", response_model=RegulatoryRetrievalResponse)
def retrieve_evidence(
    payload: RegulatoryRetrievalRequest,
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_reader),
) -> RegulatoryRetrievalResponse:
    """Retrieve evidence from already-ingested MARAS documents.

    Existing MARAS reader credentials are reused for this internal prototype.
    Shared authorization should be moved to a core security module before
    production tenant rollout.
    """
    return retrieve_regulatory_evidence(db, payload)
