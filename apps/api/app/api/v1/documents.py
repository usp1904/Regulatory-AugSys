"""Controlled document API routes."""

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.document import Document
from app.schemas.document import (
    DeletionRequestBody,
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentResponse,
)
from app.services.document_ingestion import ingest_controlled_document, request_document_deletion
from app.services.document_storage import DocumentValidationError

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
def list_documents(db: Session = Depends(get_db)) -> DocumentListResponse:
    docs = db.scalars(select(Document).order_by(Document.id.desc())).all()
    return DocumentListResponse(documents=docs)


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    uploader: str = Form(default="unknown"),
    db: Session = Depends(get_db),
) -> Document:
    try:
        return await ingest_controlled_document(db, file, uploader=uploader.strip() or "unknown")
    except DocumentValidationError as exc:
        status = 413 if "maximum size" in str(exc).lower() else 415
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(document_id: int, db: Session = Depends(get_db)) -> Document:
    document = db.scalar(
        select(Document)
        .options(
            joinedload(Document.pages),
            joinedload(Document.paragraphs),
            joinedload(Document.audit_events),
        )
        .where(Document.id == document_id)
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get("/{document_id}/download")
def download_document(document_id: int, db: Session = Depends(get_db)) -> FileResponse:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    path = Path(document.storage_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Stored file missing on disk")

    return FileResponse(
        path=path,
        filename=document.filename,
        media_type=document.content_type,
    )


@router.post("/{document_id}/deletion-request", status_code=204)
def deletion_request(
    document_id: int,
    body: DeletionRequestBody,
    db: Session = Depends(get_db),
) -> None:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    request_document_deletion(db, document, actor=body.actor, reason=body.reason)
