"""Pydantic schemas for dossier export."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ExportManifest(BaseModel):
    export_id: str
    timestamp: datetime
    dossier_id: str
    dossier_version: int
    generator_version: str
    evidence_ids: list[int]
    evidence_keys: list[str]
    document_hashes: dict[str, str]
    export_format: str
    item_count: int


class DossierExportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    export_id: str
    dossier_id: str
    dossier_version: int
    export_format: str
    file_hash: str
    byte_size: int
    content_type: str
    manifest: ExportManifest
    created_by: str
    created_at: datetime
    download_url: str


class DossierExportCreateRequest(BaseModel):
    actor: str = Field(min_length=1, max_length=256)
    format: str = Field(pattern="^(txt|docx|pdf)$")
