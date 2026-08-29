"""Immutable dossier export file records."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

EXPORT_FORMATS = frozenset({"txt", "docx", "pdf"})


class DossierExport(Base):
    __tablename__ = "dossier_exports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    export_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    dossier_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    dossier_version: Mapped[int] = mapped_column(Integer, nullable=False)
    export_format: Mapped[str] = mapped_column(String(8), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    manifest_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str] = mapped_column(String(256), nullable=False, default="unknown")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    @staticmethod
    def new_export_id() -> str:
        return f"EXP-{uuid4().hex[:16].upper()}"
