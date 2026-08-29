"""Pydantic schemas for CTD engine validation."""

from pydantic import BaseModel, Field


class CtdValidateRequest(BaseModel):
    document_ids: list[int] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    jurisdictions: list[str] = Field(default_factory=list)


class CtdValidateResponse(BaseModel):
    schemaVersion: str
    status: str
    packageStatus: str
    scope: dict
    mappings: list[dict]
    gaps: list[str]
    metrics: dict
