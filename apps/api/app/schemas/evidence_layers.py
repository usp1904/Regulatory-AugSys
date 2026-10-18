"""API schemas for regulatory truth and approved organisational interpretation."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class RegulatorySourceCreate(BaseModel):
    document_id: int = Field(gt=0)
    authority: str = Field(min_length=2, max_length=256)
    jurisdiction: str = Field(min_length=2, max_length=128)
    source_type: str = Field(min_length=2, max_length=64)
    title: str = Field(min_length=3, max_length=512)
    official_url: HttpUrl
    source_version_label: str = Field(min_length=1, max_length=128)
    publication_date: date | None = None
    effective_date: date | None = None
    review_due_date: date | None = None
    clause_id: str = Field(min_length=1, max_length=128)
    excerpt: str = Field(min_length=12, max_length=20000)
    currentness_status: Literal["UNVERIFIED", "CURRENT_VERIFIED", "SUPERSEDED", "UNDER_REVIEW"] = "UNVERIFIED"
    created_by: str = Field(min_length=1, max_length=256)


class RegulatorySourceReview(BaseModel):
    reviewer: str = Field(min_length=1, max_length=256)
    decision: Literal["APPROVED", "REJECTED", "NEEDS_UPDATE"]
    rationale: str = Field(min_length=8, max_length=4000)
    currentness_status: Literal["UNVERIFIED", "CURRENT_VERIFIED", "SUPERSEDED", "UNDER_REVIEW"] = "UNVERIFIED"


class RegulatorySourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source_key: str
    document_id: int
    document_version: int
    file_hash: str
    authority: str
    jurisdiction: str
    source_type: str
    title: str
    official_url: str
    source_version_label: str
    publication_date: date | None
    effective_date: date | None
    review_due_date: date | None
    clause_id: str
    excerpt: str
    source_status: str
    currentness_status: str
    created_by: str
    reviewer: str | None
    review_rationale: str | None
    reviewed_at: datetime | None
    created_at: datetime | None
    updated_at: datetime | None


class InterpretationCreate(BaseModel):
    source_id: int = Field(gt=0)
    obligation_id: int | None = Field(default=None, gt=0)
    interpretation: str = Field(min_length=12, max_length=12000)
    applicability: Literal["APPLICABLE", "NOT_APPLICABLE", "NEEDS_CLARIFICATION"]
    rationale: str = Field(min_length=12, max_length=8000)
    decision_owner: str = Field(min_length=1, max_length=256)
    created_by: str = Field(min_length=1, max_length=256)


class InterpretationReview(BaseModel):
    reviewer: str = Field(min_length=1, max_length=256)
    decision: Literal["CONFIRMED", "REJECTED", "NEEDS_CLARIFICATION"]
    rationale: str = Field(min_length=8, max_length=4000)


class InterpretationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    interpretation_key: str
    source_id: int
    obligation_id: int | None
    interpretation: str
    applicability: str
    rationale: str
    decision_owner: str
    status: str
    created_by: str
    reviewer: str | None
    review_rationale: str | None
    reviewed_at: datetime | None
    created_at: datetime | None
    updated_at: datetime | None
