"""API endpoints for controlled regulatory source truth and interpretations."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.requirements_mapping import require_mapping_reader, require_mapping_reviewer, require_mapping_writer
from app.core.database import get_db
from app.models.approved_interpretation import ApprovedInterpretation
from app.models.regulatory_source import RegulatorySource
from app.schemas.evidence_layers import (
    InterpretationCreate,
    InterpretationResponse,
    InterpretationReview,
    RegulatorySourceCreate,
    RegulatorySourceResponse,
    RegulatorySourceReview,
)
from app.services.evidence_layers import (
    EvidenceLayerError,
    create_interpretation,
    create_regulatory_source,
    list_interpretations,
    list_regulatory_sources,
    review_interpretation,
    review_regulatory_source,
)

router = APIRouter(prefix="/evidence-layers", tags=["regulatory-truth-and-interpretation"])


@router.post("/sources", response_model=RegulatorySourceResponse, status_code=201)
def register_regulatory_source(
    payload: RegulatorySourceCreate,
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_writer),
) -> RegulatorySource:
    try:
        return create_regulatory_source(db, payload)
    except EvidenceLayerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/sources", response_model=list[RegulatorySourceResponse])
def get_regulatory_sources(
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_reader),
) -> list[RegulatorySource]:
    return list_regulatory_sources(db)


@router.get("/sources/{source_id}", response_model=RegulatorySourceResponse)
def get_regulatory_source(
    source_id: int,
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_reader),
) -> RegulatorySource:
    source = db.get(RegulatorySource, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Regulatory source not found")
    return source


@router.post("/sources/{source_id}/review", response_model=RegulatorySourceResponse)
def review_source(
    source_id: int,
    payload: RegulatorySourceReview,
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_reviewer),
) -> RegulatorySource:
    source = db.get(RegulatorySource, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Regulatory source not found")
    try:
        return review_regulatory_source(db, source, payload)
    except EvidenceLayerError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/interpretations", response_model=InterpretationResponse, status_code=201)
def register_interpretation(
    payload: InterpretationCreate,
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_writer),
) -> ApprovedInterpretation:
    try:
        return create_interpretation(db, payload)
    except EvidenceLayerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/interpretations", response_model=list[InterpretationResponse])
def get_interpretations(
    source_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_reader),
) -> list[ApprovedInterpretation]:
    return list_interpretations(db, source_id=source_id)


@router.get("/interpretations/{interpretation_id}", response_model=InterpretationResponse)
def get_interpretation(
    interpretation_id: int,
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_reader),
) -> ApprovedInterpretation:
    item = db.get(ApprovedInterpretation, interpretation_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Interpretation not found")
    return item


@router.post("/interpretations/{interpretation_id}/review", response_model=InterpretationResponse)
def review_organisational_interpretation(
    interpretation_id: int,
    payload: InterpretationReview,
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_reviewer),
) -> ApprovedInterpretation:
    item = db.get(ApprovedInterpretation, interpretation_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Interpretation not found")
    try:
        return review_interpretation(db, item, payload)
    except EvidenceLayerError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
