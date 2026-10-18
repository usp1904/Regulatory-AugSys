"""Registry of versioned regulatory source material and source-review status."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RegulatorySource(Base):
    __tablename__ = "regulatory_sources"
    __table_args__ = (
        UniqueConstraint(
            "document_id", "document_version", "clause_id",
            name="uq_regulatory_source_document_version_clause",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    document_version: Mapped[int] = mapped_column(Integer, nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    authority: Mapped[str] = mapped_column(String(256), nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(128), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    official_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    source_version_label: Mapped[str] = mapped_column(String(128), nullable=False)
    publication_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    review_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    clause_id: Mapped[str] = mapped_column(String(128), nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    source_status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING_REVIEW", index=True)
    currentness_status: Mapped[str] = mapped_column(String(32), nullable=False, default="UNVERIFIED")
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    reviewer: Mapped[str | None] = mapped_column(String(256), nullable=True)
    review_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
