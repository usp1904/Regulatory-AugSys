from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ObligationExtractionRequest(BaseModel):
    requested_by: str = Field(min_length=1, max_length=256)


class ObligationReviewRequest(BaseModel):
    reviewer: str = Field(min_length=1, max_length=256)
    decision: Literal["APPROVED", "REJECTED"]
    rationale: str = Field(min_length=8, max_length=8000)


class ExtractedObligationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    obligation_key: str
    source_document_id: int
    mapping_id: int | None = None
    source_version: int
    source_file_hash: str
    clause_id: str
    segment_index: int
    excerpt: str
    trigger_terms: str
    extraction_method: str
    confidence: float
    status: str
    reviewer: str | None
    review_rationale: str | None
    created_at: datetime | None
    updated_at: datetime | None
    reviewed_at: datetime | None
