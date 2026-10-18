"""Heuristic obligation candidates extracted from controlled source documents."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ExtractedObligation(Base):
    __tablename__ = "extracted_obligations"
    __table_args__ = (
        UniqueConstraint(
            "source_document_id",
            "source_version",
            "clause_id",
            name="uq_extracted_obligation_source_clause_version",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    obligation_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    source_document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mapping_id: Mapped[int | None] = mapped_column(
        ForeignKey("requirements_mappings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_version: Mapped[int] = mapped_column(Integer, nullable=False)
    source_file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    clause_id: Mapped[str] = mapped_column(String(128), nullable=False)
    segment_index: Mapped[int] = mapped_column(Integer, nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    trigger_terms: Mapped[str] = mapped_column(String(512), nullable=False)
    extraction_method: Mapped[str] = mapped_column(String(64), nullable=False, default="RULE_BASED_V1")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT", index=True)
    reviewer: Mapped[str | None] = mapped_column(String(256), nullable=True)
    review_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
