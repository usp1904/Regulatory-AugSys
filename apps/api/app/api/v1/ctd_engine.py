"""CTD engine validation API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.document import Document
from app.schemas.ctd_engine import CtdValidateRequest, CtdValidateResponse
from app.services.ctd_validation import validate_ctd_documents

router = APIRouter(prefix="/ctd-engine", tags=["ctd-engine"])


@router.post("/validate", response_model=CtdValidateResponse)
def validate_ctd(
    body: CtdValidateRequest,
    db: Session = Depends(get_db),
) -> CtdValidateResponse:
    if not body.document_ids:
        raise HTTPException(status_code=400, detail="At least one document_id is required")

    docs = db.scalars(
        select(Document)
        .options(joinedload(Document.pages), joinedload(Document.paragraphs))
        .where(Document.id.in_(body.document_ids))
    ).unique().all()
    if len(docs) != len(set(body.document_ids)):
        raise HTTPException(status_code=404, detail="One or more documents not found")

    result = validate_ctd_documents(docs, body.frameworks, body.jurisdictions)
    return CtdValidateResponse(**result)
