"""In-house document API routes."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.document import Document
from app.schemas.document import DocumentListResponse, DocumentResponse
from app.services.document_storage import save_upload

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
def list_documents(db: Session = Depends(get_db)) -> DocumentListResponse:
    docs = db.scalars(select(Document).order_by(Document.id.desc())).all()
    return DocumentListResponse(documents=docs)


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Document:
    try:
        filename, file_hash, storage_path, parse_status, _size = await save_upload(file)
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc

    existing = db.scalar(select(Document).where(Document.file_hash == file_hash))
    if existing:
        return existing

    from pathlib import Path

    from app.services.document_storage import extract_text

    data = Path(storage_path).read_bytes()
    parse_status, excerpt = extract_text(filename, data)

    doc = Document(
        filename=filename,
        content_type=file.content_type or "application/octet-stream",
        file_hash=file_hash,
        storage_path=storage_path,
        parse_status=parse_status,
        text_excerpt=excerpt or None,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc
