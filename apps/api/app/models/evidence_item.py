"""Evidence capture and human review records."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

EVIDENCE_TYPES = frozenset(
    {
        "DIRECT_EVIDENCE",
        "SUMMARY_EVIDENCE",
        "REFERENCE_ONLY",
        "CONFIDENTIAL_REFERENCE",
        "GAP",
    }
)
REVIEW_STATUSES = frozenset({"PENDING", "APPROVED", "REJECTED", "NEEDS_CLARIFICATION"})
GAP_EXPORT_TYPES = frozenset({"GAP", "CONFIDENTIAL_REFERENCE"})

if TYPE_CHECKING:
    from app.models.document import Document


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evidence_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    evidence_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    dossier_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    ctd_section_code: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    source_document_id: Mapped[int | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_document_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    paragraph_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    exact_source_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_type: Mapped[str] = mapped_column(String(32), nullable=False)
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    reviewer: Mapped[str | None] = mapped_column(String(256), nullable=True)
    reviewer_decision: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reviewer_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    supersedes_id: Mapped[int | None] = mapped_column(
        ForeignKey("evidence_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by: Mapped[str] = mapped_column(String(256), nullable=False, default="unknown")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    source_document: Mapped[Document | None] = relationship("Document")

    @staticmethod
    def new_evidence_key() -> str:
        return f"EV-{uuid4().hex[:16].upper()}"
