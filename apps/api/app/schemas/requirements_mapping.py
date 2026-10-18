"""Request and response schemas for requirements mapping."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

REVIEW_DECISIONS = frozenset({"APPROVED", "CHANGES_REQUIRED", "REJECTED"})


class RequirementsMappingCreateRequest(BaseModel):
    dossier_id: str = Field(min_length=1, max_length=128)
    created_by: str = Field(min_length=1, max_length=256)
    source_document_id: int = Field(gt=0)
    data: dict[str, Any]

    @field_validator("data")
    @classmethod
    def require_mapping_sections(cls, value: dict[str, Any]) -> dict[str, Any]:
        for key in ("source", "system", "clarification", "pbi"):
            if not isinstance(value.get(key), dict):
                raise ValueError(f"data.{key} must be an object")
        return value


class RequirementsMappingReviewRequest(BaseModel):
    reviewer: str = Field(min_length=1, max_length=256)
    decision: str
    rationale: str = Field(min_length=1, max_length=4000)

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, value: str) -> str:
        if value not in REVIEW_DECISIONS:
            raise ValueError(f"decision must be one of {sorted(REVIEW_DECISIONS)}")
        return value


class RequirementsMappingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mapping_key: str
    dossier_id: str
    data: dict[str, Any]
    readiness_status: str
    blockers: list[str]
    review_status: str
    created_by: str
    reviewer: str | None
    reviewer_decision: str | None
    reviewer_rationale: str | None
    created_at: datetime | None
    updated_at: datetime | None
    reviewed_at: datetime | None
