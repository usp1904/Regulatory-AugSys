"""Pydantic schemas for controlled document ingestion."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentPageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page_number: int
    text_content: str


class DocumentParagraphResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    paragraph_index: int
    text_content: str


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    actor: str
    detail: str | None
    created_at: datetime


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    content_type: str
    byte_size: int
    file_hash: str
    version: int
    uploader: str
    parse_status: str
    text_excerpt: str | None
    extraction_error: str | None
    created_at: datetime


class DocumentDetailResponse(DocumentResponse):
    pages: list[DocumentPageResponse] = Field(default_factory=list)
    paragraphs: list[DocumentParagraphResponse] = Field(default_factory=list)
    audit_events: list[AuditEventResponse] = Field(default_factory=list)


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]


class DeletionRequestBody(BaseModel):
    actor: str = Field(min_length=1, max_length=256)
    reason: str = Field(min_length=1, max_length=2000)
