"""Controlled document ingestion orchestration."""

from __future__ import annotations

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentPage, DocumentParagraph
from app.services.audit import record_audit_event
from app.services.document_extraction import extract_document
from app.services.document_storage import (
    persist_original_bytes,
    read_upload_bytes,
    validate_upload_metadata,
)

EXCERPT_LIMIT = 8000


async def ingest_controlled_document(
    db: Session,
    file: UploadFile,
    uploader: str,
) -> Document:
    filename = file.filename or "upload.bin"
    data = await read_upload_bytes(file)
    media_type = validate_upload_metadata(filename, file.content_type, len(data))

    stored = persist_original_bytes(filename, data, media_type)
    existing = db.scalar(select(Document).where(Document.file_hash == stored.file_hash))
    if existing:
        record_audit_event(
            db,
            event_type="upload",
            actor=uploader,
            document_id=existing.id,
            detail={"filename": stored.filename, "deduplicated": True},
        )
        db.commit()
        db.refresh(existing)
        return existing

    next_version = db.scalar(
        select(func.coalesce(func.max(Document.version), 0)).where(
            Document.filename == stored.filename
        )
    )
    version = int(next_version or 0) + 1

    document = Document(
        filename=stored.filename,
        content_type=media_type,
        byte_size=stored.byte_size,
        file_hash=stored.file_hash,
        storage_path=stored.storage_path,
        version=version,
        uploader=uploader,
        parse_status="PENDING",
    )
    db.add(document)
    db.flush()

    record_audit_event(
        db,
        event_type="upload",
        actor=uploader,
        document_id=document.id,
        detail={
            "filename": stored.filename,
            "media_type": media_type,
            "byte_size": stored.byte_size,
            "file_hash": stored.file_hash,
            "version": version,
        },
    )

    extraction = extract_document(media_type, data)
    if extraction.status == "EXTRACTED":
        for index, page_text in enumerate(extraction.pages, start=1):
            db.add(
                DocumentPage(
                    document_id=document.id,
                    page_number=index,
                    text_content=page_text,
                )
            )
        for index, paragraph_text in enumerate(extraction.paragraphs):
            db.add(
                DocumentParagraph(
                    document_id=document.id,
                    paragraph_index=index,
                    text_content=paragraph_text,
                )
            )
        document.parse_status = "EXTRACTED"
        document.text_excerpt = extraction.full_text[:EXCERPT_LIMIT] or None
        record_audit_event(
            db,
            event_type="extraction_success",
            actor=uploader,
            document_id=document.id,
            detail={
                "page_count": len(extraction.pages),
                "paragraph_count": len(extraction.paragraphs),
            },
        )
    else:
        document.parse_status = extraction.status
        document.extraction_error = extraction.error
        record_audit_event(
            db,
            event_type="extraction_failure",
            actor=uploader,
            document_id=document.id,
            detail={"error": extraction.error, "status": extraction.status},
        )

    db.commit()
    db.refresh(document)
    return document


def request_document_deletion(db: Session, document: Document, actor: str, reason: str) -> None:
    record_audit_event(
        db,
        event_type="deletion_request",
        actor=actor,
        document_id=document.id,
        detail={"filename": document.filename, "reason": reason},
    )
    db.commit()
