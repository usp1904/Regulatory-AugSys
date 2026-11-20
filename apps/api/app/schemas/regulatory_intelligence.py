"""Contracts for the MARAS Regulatory Intelligence retrieval slice."""

from pydantic import BaseModel, Field


class RegulatoryRetrievalRequest(BaseModel):
    query: str = Field(min_length=3, max_length=2000)
    document_ids: list[int] | None = Field(default=None, max_length=100)
    top_k: int = Field(default=8, ge=1, le=20)


class RegulatoryEvidenceItem(BaseModel):
    document_id: int
    filename: str
    document_version: int
    file_hash: str
    location_type: str
    location: str
    excerpt: str
    score: float


class RegulatoryRetrievalResponse(BaseModel):
    status: str
    query: str
    results: list[RegulatoryEvidenceItem]
    message: str
