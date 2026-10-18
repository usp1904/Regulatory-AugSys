"""Requirements mapping persistence and independent review routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.requirements_mapping import RequirementsMapping
from app.schemas.requirements_mapping import (
    RequirementsMappingCreateRequest,
    RequirementsMappingResponse,
    RequirementsMappingReviewRequest,
    RequirementsMappingUpdateRequest,
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


@router.post("", response_model=RequirementsMappingResponse, status_code=201)
def create_requirements_mapping(
    payload: RequirementsMappingCreateRequest,
    db: Session = Depends(get_db),
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
) -> list[dict]:
    return [mapping_to_response(item) for item in list_mappings(db, dossier_id)]


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
) -> dict:
    item = db.get(RequirementsMapping, mapping_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Requirements mapping not found")
    try:
        reviewed = review_mapping(db, item, payload)
    except RequirementsMappingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return mapping_to_response(reviewed)
