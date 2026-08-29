"""Pydantic schemas for evidence capture and review."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.evidence_item import EVIDENCE_TYPES

REVIEW_DECISIONS = frozenset({"APPROVED", "REJECTED", "NEEDS_CLARIFICATION"})


class EvidenceCreateRequest(BaseModel):
    dossier_id: str = Field(min_length=1, max_length=128)
    ctd_section_code: str | None = Field(default=None, max_length=32)
    source_document_id: int | None = None
    page_number: int | None = Field(default=None, ge=1)
    paragraph_index: int | None = Field(default=None, ge=0)
    exact_source_excerpt: str = Field(min_length=1)
    normalized_summary: str | None = None
    evidence_type: str
    created_by: str = Field(min_length=1, max_length=256)

    @field_validator("evidence_type")
    @classmethod
    def validate_evidence_type(cls, value: str) -> str:
        if value not in EVIDENCE_TYPES:
            raise ValueError(f"evidence_type must be one of {sorted(EVIDENCE_TYPES)}")
        return value


class EvidenceUpdateRequest(BaseModel):
    actor: str = Field(min_length=1, max_length=256)
    ctd_section_code: str | None = Field(default=None, max_length=32)
    exact_source_excerpt: str | None = None
    normalized_summary: str | None = None
    evidence_type: str | None = None

    @field_validator("evidence_type")
    @classmethod
    def validate_evidence_type(cls, value: str | None) -> str | None:
        if value is not None and value not in EVIDENCE_TYPES:
            raise ValueError(f"evidence_type must be one of {sorted(EVIDENCE_TYPES)}")
        return value


class EvidenceReviewRequest(BaseModel):
    reviewer: str = Field(min_length=1, max_length=256)
    decision: str
    rationale: str = Field(min_length=1)

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, value: str) -> str:
        if value not in REVIEW_DECISIONS:
            raise ValueError(f"decision must be one of {sorted(REVIEW_DECISIONS)}")
        return value


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    evidence_key: str
    evidence_version: int
    dossier_id: str
    ctd_section_code: str | None
    source_document_id: int | None
    source_document_version: int | None
    page_number: int | None
    paragraph_index: int | None
    exact_source_excerpt: str
    normalized_summary: str | None
    evidence_type: str
    review_status: str
    reviewer: str | None
    reviewer_decision: str | None
    reviewer_rationale: str | None
    supersedes_id: int | None
    created_by: str
    created_at: datetime
    updated_at: datetime
    reviewed_at: datetime | None
    excerpt_locked: bool = False


class EvidenceListResponse(BaseModel):
    items: list[EvidenceResponse]


class EvidenceExportItem(BaseModel):
    evidence_key: str
    evidence_version: int
    dossier_id: str
    ctd_section_code: str | None
    evidence_type: str
    export_label: str
    exact_source_excerpt: str | None = None
    normalized_summary: str | None = None
    source_document_id: int | None = None
    source_document_version: int | None = None
    page_number: int | None = None
    reviewer: str | None = None
    reviewed_at: datetime | None = None


class EvidenceExportResponse(BaseModel):
    package_status: str = "DRAFT_NOT_CONTROLLED"
    dossier_id: str
    approved_only: bool = True
    items: list[EvidenceExportItem]
