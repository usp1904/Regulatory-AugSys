"""Contracts for the MARAS Regulatory Intelligence engine."""

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
    chunk_id: str
    location_type: str
    location: str
    excerpt: str
    score: float


class RegulatoryRetrievalResponse(BaseModel):
    status: str
    query: str
    results: list[RegulatoryEvidenceItem]
    message: str


class RegulatoryIndexRequest(BaseModel):
    document_id: int = Field(gt=0)


class RegulatoryIndexResponse(BaseModel):
    document_id: int
    document_version: int
    file_hash: str
    chunk_count: int
    entity_count: int
    edge_count: int
    vector_count: int
    graph_persisted: bool
    provider_status: str



class RegulatoryQueryResponse(BaseModel):
    status: str
    query: str
    retrieval_mode: str
    results: list[RegulatoryEvidenceItem]
    message: str
    plan: dict
    trace: list[dict]
    generation_status: str
    answer_mode: str
    answer_text: str
    claims: list[dict]
    validation_status: str
    disclaimer: str
