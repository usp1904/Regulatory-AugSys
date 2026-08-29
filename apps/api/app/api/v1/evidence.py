"""Evidence capture and human review API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.document import Document
from app.models.evidence_item import EvidenceItem
from app.schemas.evidence import (
    EvidenceCreateRequest,
    EvidenceExportResponse,
    EvidenceListResponse,
    EvidenceResponse,
    EvidenceReviewRequest,
    EvidenceUpdateRequest,
)
from app.services.evidence import (
    EvidenceServiceError,
    create_evidence,
    evidence_to_response,
    export_approved_evidence,
    list_evidence,
    review_evidence,
    update_evidence,
)

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.post("", response_model=EvidenceResponse, status_code=201)
def create_evidence_item(
    payload: EvidenceCreateRequest,
    db: Session = Depends(get_db),
) -> EvidenceResponse:
    try:
        item = create_evidence(db, payload)
    except EvidenceServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return evidence_to_response(item)


@router.get("", response_model=EvidenceListResponse)
def list_evidence_items(
    dossier_id: str | None = Query(default=None),
    ctd_section_code: str | None = Query(default=None),
    review_status: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> EvidenceListResponse:
    try:
        items = list_evidence(
            db,
            dossier_id=dossier_id,
            ctd_section_code=ctd_section_code,
            review_status=review_status,
        )
    except EvidenceServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return EvidenceListResponse(items=[evidence_to_response(item) for item in items])


@router.get("/export", response_model=EvidenceExportResponse)
def export_evidence(
    dossier_id: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
) -> EvidenceExportResponse:
    return export_approved_evidence(db, dossier_id)


@router.get("/{evidence_id}", response_model=EvidenceResponse)
def get_evidence_item(evidence_id: int, db: Session = Depends(get_db)) -> EvidenceResponse:
    item = db.get(EvidenceItem, evidence_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return evidence_to_response(item)


@router.get("/{evidence_id}/review-context")
def get_evidence_review_context(evidence_id: int, db: Session = Depends(get_db)) -> dict:
    item = db.get(EvidenceItem, evidence_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Evidence not found")

    source_text = ""
    document = None
    if item.source_document_id:
        document = db.scalar(
            select(Document)
            .options(joinedload(Document.pages), joinedload(Document.paragraphs))
            .where(Document.id == item.source_document_id)
        )
        if document:
            if item.page_number is not None:
                page = next((p for p in document.pages if p.page_number == item.page_number), None)
                source_text = page.text_content if page else document.full_extracted_text()
            elif item.paragraph_index is not None:
                paragraph = next(
                    (p for p in document.paragraphs if p.paragraph_index == item.paragraph_index),
                    None,
                )
                source_text = (
                    paragraph.text_content if paragraph else document.full_extracted_text()
                )
            else:
                source_text = document.full_extracted_text()

    return {
        "evidence": evidence_to_response(item),
        "source_document": {
            "id": document.id,
            "filename": document.filename,
            "version": document.version,
            "file_hash": document.file_hash,
        }
        if document
        else None,
        "source_text": source_text,
    }


@router.patch("/{evidence_id}", response_model=EvidenceResponse)
def patch_evidence_item(
    evidence_id: int,
    payload: EvidenceUpdateRequest,
    db: Session = Depends(get_db),
) -> EvidenceResponse:
    item = db.get(EvidenceItem, evidence_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Evidence not found")
    try:
        updated = update_evidence(db, item, payload)
    except EvidenceServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return evidence_to_response(updated)


@router.post("/{evidence_id}/review", response_model=EvidenceResponse)
def submit_evidence_review(
    evidence_id: int,
    payload: EvidenceReviewRequest,
    db: Session = Depends(get_db),
) -> EvidenceResponse:
    item = db.get(EvidenceItem, evidence_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Evidence not found")
    try:
        reviewed = review_evidence(db, item, payload)
    except EvidenceServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return evidence_to_response(reviewed)
