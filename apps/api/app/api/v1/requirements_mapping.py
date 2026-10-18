"""Requirements mapping persistence and independent review routes."""

import hmac
import os

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.extracted_obligation import ExtractedObligation
from app.models.requirements_mapping import RequirementsMapping
from app.schemas.extracted_obligation import (
    ExtractedObligationResponse,
    ObligationExtractionRequest,
    ObligationReviewRequest,
)
from app.schemas.requirements_mapping import (
    RequirementsMappingCreateRequest,
    RequirementsMappingResponse,
    RequirementsMappingReviewRequest,
    RequirementsMappingUpdateRequest,
)
from app.services.obligation_extraction import (
    ObligationExtractionError,
    extract_obligations,
    list_obligations,
    review_obligation,
)
from app.services.requirements_mapping import (
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
