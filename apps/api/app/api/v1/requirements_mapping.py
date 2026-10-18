"""Requirements mapping persistence and independent review routes."""

import hmac
import os

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.clarification import ClarificationQuestion
from app.models.extracted_obligation import ExtractedObligation
from app.models.requirements_mapping import RequirementsMapping
from app.models.regulatory_truth import InterpretationDecision, RegulatorySourceRecord
from app.schemas.clarification import (
    ClarificationCreateRequest,
    ClarificationResponse,
    ClarificationUpdateRequest,
)
from app.schemas.extracted_obligation import (
    ExtractedObligationResponse,
    ObligationExtractionRequest,
    ObligationReviewRequest,
)
from app.schemas.regulatory_truth import (\n    InterpretationCreate,\n    InterpretationResponse,\n    InterpretationReview,\n    RegulatorySourceCreate,\n    RegulatorySourceResponse,\n    RegulatorySourceReview,\n)\nfrom app.schemas.requirements_mapping import (
    RequirementsMappingCreateRequest,
    RequirementsMappingResponse,
    RequirementsMappingReviewRequest,
    RequirementsMappingUpdateRequest,
)
from app.services.clarifications import (
    ClarificationError,
    create_question,
    get_question,
    list_questions,
    update_question,
)
from app.services.obligation_extraction import (
    ObligationExtractionError,
    create_mapping_from_obligation,
    extract_obligations,
    list_obligations,
    review_obligation,
)
from app.services.regulatory_truth import (\n    RegulatoryTruthError,\n    create_interpretation,\n    create_source_record,\n    review_interpretation,\n    review_source_record,\n)\nfrom app.services.requirements_mapping import (
    RequirementsMappingError,
    create_mapping,
    list_mappings,
    mapping_to_response,
    review_mapping,
    update_mapping,
)

router = APIRouter(prefix="/requirements-mappings", tags=["requirements-mapping"])


def _configured_key(name: str) -> str:
    key = os.getenv(name, "").strip()
    if not key:
        raise HTTPException(
            status_code=503,
            detail=f"Requirements mapping API is disabled until {name} is configured.",
        )
    return key


def require_mapping_writer(authorization: str | None = Header(default=None)) -> str:
    expected = _configured_key("MARAS_REQUIREMENTS_MAPPING_WRITE_KEY")
    supplied = authorization.removeprefix("Bearer ").strip() if authorization else ""
    if not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(
            status_code=401,
            detail="Valid mapping writer credentials are required.",
        )
    return "mapping-writer"


def require_mapping_reader(authorization: str | None = Header(default=None)) -> str:
    supplied = authorization.removeprefix("Bearer ").strip() if authorization else ""
    candidates = [
        os.getenv("MARAS_REQUIREMENTS_MAPPING_WRITE_KEY", "").strip(),
        os.getenv("MARAS_REQUIREMENTS_MAPPING_REVIEW_KEY", "").strip(),
    ]
    candidates = [key for key in candidates if key]
    if not candidates:
        raise HTTPException(
            status_code=503,
            detail="Requirements mapping API is disabled until access keys are configured.",
        )
    if not supplied or not any(hmac.compare_digest(supplied, key) for key in candidates):
        raise HTTPException(
            status_code=401,
            detail="Valid mapping access credentials are required.",
        )
    return "mapping-reader"


def require_mapping_reviewer(authorization: str | None = Header(default=None)) -> str:
    expected = _configured_key("MARAS_REQUIREMENTS_MAPPING_REVIEW_KEY")
    supplied = authorization.removeprefix("Bearer ").strip() if authorization else ""
    if not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Reviewer credentials are required.")
    return "mapping-reviewer"


@router.post("", response_model=RequirementsMappingResponse, status_code=201)
def create_requirements_mapping(
    payload: RequirementsMappingCreateRequest,
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_writer),
) -> dict:
    try:
        item = create_mapping(db, payload)
    except RequirementsMappingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return mapping_to_response(item)


@router.get("", response_model=list[RequirementsMappingResponse])
def get_requirements_mappings(
    dossier_id: str | None = Query(default=None, max_length=128),
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_reader),
) -> list[dict]:
    return [mapping_to_response(item) for item in list_mappings(db, dossier_id)]


@router.get("/clarifications", response_model=list[ClarificationResponse])
def get_clarifications(
    status: str | None = Query(default=None, max_length=32),
    mapping_id: int | None = Query(default=None, gt=0),
    dossier_id: str | None = Query(default=None, max_length=128),
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_reader),
) -> list[dict]:
    return list_questions(
        db,
        status=status,
        mapping_id=mapping_id,
        dossier_id=dossier_id,
    )


@router.get("/obligations", response_model=list[ExtractedObligationResponse])
def get_extracted_obligations(
    document_id: int | None = Query(default=None, gt=0),
    status: str | None = Query(default=None, max_length=32),
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_reader),
) -> list[ExtractedObligation]:
    return list_obligations(db, document_id=document_id, status=status)


@router.get("/{mapping_id}", response_model=RequirementsMappingResponse)
def get_requirements_mapping(
    mapping_id: int,
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_reader),
) -> dict:
    item = db.get(RequirementsMapping, mapping_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Requirements mapping not found")
    return mapping_to_response(item)


@router.put("/{mapping_id}", response_model=RequirementsMappingResponse)
def update_requirements_mapping(
    mapping_id: int,
    payload: RequirementsMappingUpdateRequest,
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_writer),
) -> dict:
    item = db.get(RequirementsMapping, mapping_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Requirements mapping not found")
    try:
        updated = update_mapping(db, item, payload)
    except RequirementsMappingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return mapping_to_response(updated)


@router.post("/{mapping_id}/review", response_model=RequirementsMappingResponse)
def review_requirements_mapping(
    mapping_id: int,
    payload: RequirementsMappingReviewRequest,
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_reviewer),
) -> dict:
    item = db.get(RequirementsMapping, mapping_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Requirements mapping not found")
    try:
        reviewed = review_mapping(db, item, payload)
    except RequirementsMappingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return mapping_to_response(reviewed)


@router.post("/clarifications", response_model=ClarificationResponse, status_code=201)
def create_clarification(
    payload: ClarificationCreateRequest,
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_writer),
) -> dict:
    try:
        return create_question(db, payload)
    except ClarificationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/clarifications/{question_id}", response_model=ClarificationResponse)
def get_clarification(
    question_id: int,
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_reader),
) -> dict:
    result = get_question(db, question_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Clarification not found")
    return result


@router.patch("/clarifications/{question_id}", response_model=ClarificationResponse)
def update_clarification(
    question_id: int,
    payload: ClarificationUpdateRequest,
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_writer),
) -> dict:
    item = db.get(ClarificationQuestion, question_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Clarification not found")
    try:
        return update_question(db, item, payload)
    except ClarificationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc



@router.post(
    "/obligations/extract/{document_id}",
    response_model=list[ExtractedObligationResponse],
)
def run_obligation_extraction(
    document_id: int,
    payload: ObligationExtractionRequest,
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_writer),
) -> list[ExtractedObligation]:
    try:
        return extract_obligations(db, document_id, payload)
    except ObligationExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put(
    "/obligations/{obligation_id}/review",
    response_model=ExtractedObligationResponse,
)
def review_extracted_obligation(
    obligation_id: int,
    payload: ObligationReviewRequest,
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_reviewer),
) -> ExtractedObligation:
    item = db.get(ExtractedObligation, obligation_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Obligation candidate not found")
    try:
        return review_obligation(db, item, payload)
    except ObligationExtractionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/obligations/{obligation_id}/create-mapping",
    response_model=RequirementsMappingResponse,
)
def create_mapping_from_extracted_obligation(
    obligation_id: int,
    created_by: str = Query(min_length=1, max_length=256),
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_writer),
) -> dict:
    item = db.get(ExtractedObligation, obligation_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Obligation candidate not found")
    try:
        mapping = create_mapping_from_obligation(db, item, created_by=created_by)
    except ObligationExtractionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return mapping_to_response(mapping)



# Layer 1: controlled regulatory source metadata and explicit human verification.
@router.post(
    "/regulatory-sources",
    response_model=RegulatorySourceResponse,
    status_code=201,
)
def create_regulatory_source(
    payload: RegulatorySourceCreate,
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_writer),
) -> RegulatorySourceRecord:
    try:
        return create_source_record(db, payload)
    except RegulatoryTruthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/regulatory-sources",
    response_model=list[RegulatorySourceResponse],
)
def list_regulatory_sources(
    document_id: int | None = Query(default=None, gt=0),
    source_status: str | None = Query(default=None, max_length=32),
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_reader),
) -> list[RegulatorySourceRecord]:
    query = db.query(RegulatorySourceRecord).order_by(RegulatorySourceRecord.created_at.desc())
    if document_id is not None:
        query = query.filter(RegulatorySourceRecord.document_id == document_id)
    if source_status:
        query = query.filter(RegulatorySourceRecord.source_status == source_status)
    return query.all()


@router.put(
    "/regulatory-sources/{source_id}/review",
    response_model=RegulatorySourceResponse,
)
def review_regulatory_source(
    source_id: int,
    payload: RegulatorySourceReview,
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_reviewer),
) -> RegulatorySourceRecord:
    item = db.get(RegulatorySourceRecord, source_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Regulatory source record not found")
    try:
        return review_source_record(db, item, payload)
    except RegulatoryTruthError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


# Layer 2: organisation-specific interpretation is separate from source truth.
@router.post(
    "/interpretations",
    response_model=InterpretationResponse,
    status_code=201,
)
def submit_interpretation(
    payload: InterpretationCreate,
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_writer),
) -> InterpretationDecision:
    try:
        return create_interpretation(db, payload)
    except RegulatoryTruthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/interpretations",
    response_model=list[InterpretationResponse],
)
def list_interpretations(
    obligation_id: int | None = Query(default=None, gt=0),
    status: str | None = Query(default=None, max_length=32),
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_reader),
) -> list[InterpretationDecision]:
    query = db.query(InterpretationDecision).order_by(
        InterpretationDecision.obligation_id, InterpretationDecision.version.desc()
    )
    if obligation_id is not None:
        query = query.filter(InterpretationDecision.obligation_id == obligation_id)
    if status:
        query = query.filter(InterpretationDecision.status == status)
    return query.all()


@router.put(
    "/interpretations/{interpretation_id}/review",
    response_model=InterpretationResponse,
)
def review_organisational_interpretation(
    interpretation_id: int,
    payload: InterpretationReview,
    db: Session = Depends(get_db),
    _access: str = Depends(require_mapping_reviewer),
) -> InterpretationDecision:
    item = db.get(InterpretationDecision, interpretation_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Interpretation decision not found")
    try:
        return review_interpretation(db, item, payload)
    except RegulatoryTruthError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
