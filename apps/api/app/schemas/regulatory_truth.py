"""API schemas for regulatory source truth and interpretation decisions."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RegulatorySourceCreate(BaseModel):
    document_id: int = Field(gt=0)
    title: str = Field(min_length=3, max_length=512)
    issuing_authority: str = Field(min_length=2, max_length=256)
    jurisdiction: str = Field(min_length=2, max_length=256)
    document_type: str = Field(min_length=2, max_length=128)
    official_url: str = Field(min_length=8, max_length=2048)
    version_label: str = Field(min_length=1, max_length=128)
    publication_date: date | None = None
    effective_date: date | None = None
    applicability_scope: str = Field(min_length=8, max_length=8000)
    created_by: str = Field(min_length=1, max_length=256)

    @field_validator("official_url")
    @classmethod
    def require_https(cls, value: str) -> str:
        if not value.strip().lower().startswith("https://"):
            raise ValueError("official_url must use HTTPS")
        return value.strip()


class RegulatorySourceReview(BaseModel):
    reviewer: str = Field(min_length=1, max_length=256)
    decision: Literal["VERIFIED", "REJECTED", "STALE"]
    rationale: str = Field(min_length=8, max_length=4000)


class RegulatorySourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    document_id: int
    title: str
    issuing_authority: str
    jurisdiction: str
    document_type: str
    official_url: str
    version_label: str
    publication_date: date | None
    effective_date: date | None
    applicability_scope: str
    content_hash: str
    source_status: str
    created_by: str
    verification_rationale: str | None
    verified_by: str | None
    verified_at: datetime | None
    created_at: datetime | None
    updated_at: datetime | None


class InterpretationCreate(BaseModel):
    obligation_id: int = Field(gt=0)
    interpretation: str = Field(min_length=12, max_length=8000)
    applicability: Literal["APPLICABLE", "NOT_APPLICABLE", "PARTIALLY_APPLICABLE", "UNDECIDED"]
    rationale: str = Field(min_length=8, max_length=4000)
    assumptions: str = Field(default="", max_length=4000)
    unresolved_questions: str = Field(default="", max_length=4000)
    decision_owner: str = Field(min_length=1, max_length=256)
    submitted_by: str = Field(min_length=1, max_length=256)
    supersedes_id: int | None = Field(default=None, gt=0)


class InterpretationReview(BaseModel):
    reviewer: str = Field(min_length=1, max_length=256)
    reviewer_role: str = Field(min_length=2, max_length=128)
    decision: Literal["APPROVED", "REJECTED", "NEEDS_CLARIFICATION"]
    rationale: str = Field(min_length=8, max_length=4000)


class InterpretationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    obligation_id: int
    version: int
    interpretation: str
    applicability: str
    rationale: str
    assumptions: str
    unresolved_questions: str
    decision_owner: str
    status: str
    submitted_by: str
    reviewed_by: str | None
    reviewer_role: str | None
    review_rationale: str | None
    approved_at: datetime | None
    supersedes_id: int | None
    created_at: datetime | None
    updated_at: datetime | None
