from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ClarificationCreateRequest(BaseModel):
    mapping_id: int = Field(gt=0)
    question: str = Field(min_length=8, max_length=8000)
    owner: str = Field(min_length=1, max_length=256)
    created_by: str = Field(min_length=1, max_length=256)
    due_date: date | None = None


class ClarificationUpdateRequest(BaseModel):
    actor: str = Field(min_length=1, max_length=256)
    action: str
    answer: str | None = Field(default=None, max_length=12000)
    decision: str | None = Field(default=None, max_length=8000)
    rationale: str | None = Field(default=None, max_length=8000)
    owner: str | None = Field(default=None, max_length=256)
    due_date: date | None = None


class ClarificationHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    action: str
    actor: str
    snapshot: dict[str, Any]
    created_at: datetime | None


class ClarificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    question_key: str
    mapping_id: int
    dossier_id: str
    mapping_key: str
    question: str
    owner: str
    created_by: str
    status: str
    answer: str | None
    answered_by: str | None
    decision: str | None
    rationale: str | None
    due_date: date | None
    resolved_by: str | None
    created_at: datetime | None
    updated_at: datetime | None
    resolved_at: datetime | None
    history: list[ClarificationHistoryResponse]
