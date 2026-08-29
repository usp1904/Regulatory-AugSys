"""Pydantic schemas for document uploads."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    content_type: str
    file_hash: str
    parse_status: str
    text_excerpt: str | None
    created_at: datetime


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
