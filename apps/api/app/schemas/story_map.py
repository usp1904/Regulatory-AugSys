"""Pydantic schemas for Story Map workspace."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.story_map import (
    GROUP_BY_OPTIONS,
    RELEASE_MEANINGS,
    STORY_MAP_TEMPLATES,
    STORY_STATUSES,
    TRACE_LINK_TYPES,
    TRACE_SOURCE_WORKSPACES,
)


class TraceLinkCreateRequest(BaseModel):
    link_type: str
    external_ref: str = Field(min_length=1, max_length=512)
    label: str = Field(min_length=1, max_length=512)
    source_workspace: str

    @field_validator("link_type")
    @classmethod
    def validate_link_type(cls, value: str) -> str:
        if value not in TRACE_LINK_TYPES:
            raise ValueError(f"link_type must be one of {sorted(TRACE_LINK_TYPES)}")
        return value

    @field_validator("source_workspace")
    @classmethod
    def validate_source_workspace(cls, value: str) -> str:
        if value not in TRACE_SOURCE_WORKSPACES:
            raise ValueError(f"source_workspace must be one of {sorted(TRACE_SOURCE_WORKSPACES)}")
        return value


class TraceLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    link_type: str
    external_ref: str
    label: str
    source_workspace: str
    created_at: datetime


class BackboneCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=256)
    sort_order: int = Field(default=0, ge=0)


class BackboneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    sort_order: int


class ReleaseSliceCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    release_meaning: str
    description: str | None = None
    sort_order: int = Field(default=0, ge=0)

    @field_validator("release_meaning")
    @classmethod
    def validate_release_meaning(cls, value: str) -> str:
        if value not in RELEASE_MEANINGS:
            raise ValueError(f"release_meaning must be one of {sorted(RELEASE_MEANINGS)}")
        return value


class ReleaseSliceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    release_meaning: str
    description: str | None
    sort_order: int


class StoryCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    backbone_id: int | None = None
    release_slice_id: int | None = None
    sort_order: int = Field(default=0, ge=0)
    group_key: str | None = Field(default=None, max_length=256)
    owner: str | None = Field(default=None, max_length=256)
    outcome_or_obligation: str | None = None
    acceptance_criteria: str | None = None
    evidence_required: str | None = None
    risk: str | None = None
    dependency: str | None = None
    source_control_ref: str | None = None
    status: str = "planned"

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in STORY_STATUSES:
            raise ValueError(f"status must be one of {sorted(STORY_STATUSES)}")
        return value


class StoryUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=512)
    backbone_id: int | None = None
    release_slice_id: int | None = None
    sort_order: int | None = Field(default=None, ge=0)
    group_key: str | None = Field(default=None, max_length=256)
    owner: str | None = Field(default=None, max_length=256)
    outcome_or_obligation: str | None = None
    acceptance_criteria: str | None = None
    evidence_required: str | None = None
    risk: str | None = None
    dependency: str | None = None
    source_control_ref: str | None = None
    status: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in STORY_STATUSES:
            raise ValueError(f"status must be one of {sorted(STORY_STATUSES)}")
        return value


class StoryReorderRequest(BaseModel):
    story_ids: list[int] = Field(min_length=1)


class StoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    backbone_id: int | None
    release_slice_id: int | None
    sort_order: int
    group_key: str | None
    owner: str | None
    outcome_or_obligation: str | None
    acceptance_criteria: str | None
    evidence_required: str | None
    risk: str | None
    dependency: str | None
    source_control_ref: str | None
    status: str
    trace_links: list[TraceLinkResponse] = []
    created_at: datetime
    updated_at: datetime


class StoryMapCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=256)
    template: str
    intent: str = ""
    group_by: str = "outcome"
    created_by: str = Field(min_length=1, max_length=256)

    @field_validator("template")
    @classmethod
    def validate_template(cls, value: str) -> str:
        if value not in STORY_MAP_TEMPLATES:
            raise ValueError(f"template must be one of {sorted(STORY_MAP_TEMPLATES)}")
        return value

    @field_validator("group_by")
    @classmethod
    def validate_group_by(cls, value: str) -> str:
        if value not in GROUP_BY_OPTIONS:
            raise ValueError(f"group_by must be one of {sorted(GROUP_BY_OPTIONS)}")
        return value


class StoryMapUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=256)
    intent: str | None = None
    group_by: str | None = None

    @field_validator("group_by")
    @classmethod
    def validate_group_by(cls, value: str | None) -> str | None:
        if value is not None and value not in GROUP_BY_OPTIONS:
            raise ValueError(f"group_by must be one of {sorted(GROUP_BY_OPTIONS)}")
        return value


class StoryMapResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    map_key: str
    title: str
    template: str
    intent: str
    group_by: str
    package_status: str
    created_by: str
    backbones: list[BackboneResponse] = []
    release_slices: list[ReleaseSliceResponse] = []
    stories: list[StoryResponse] = []
    created_at: datetime
    updated_at: datetime


class StoryMapListResponse(BaseModel):
    items: list[StoryMapResponse]


class StoryMapExportResponse(BaseModel):
    schema_version: str = "maras.story-map.v1"
    package_status: str = "DRAFT_NOT_CONTROLLED"
    disclaimer: str = (
        "Draft story map for SME/QA review only. "
        "Not submission-ready evidence or final regulatory interpretation."
    )
    story_map: StoryMapResponse


class LinkableCtdSection(BaseModel):
    code: str
    title: str
    module: str | None = None


class LinkableEvidenceItem(BaseModel):
    id: int
    evidence_key: str
    dossier_id: str
    ctd_section_code: str | None
    review_status: str
    evidence_type: str


class LinkableSourcesResponse(BaseModel):
    ctd_sections: list[LinkableCtdSection]
    evidence_items: list[LinkableEvidenceItem]
