"""Authoritative source metadata and human-approved organisational interpretations."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RegulatorySourceRecord(Base):
    __tablename__ = "regulatory_source_records"
    __table_args__ = (
        UniqueConstraint("document_id", name="uq_regulatory_source_document"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    issuing_authority: Mapped[str] = mapped_column(String(256), nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(256), nullable=False)
    document_type: Mapped[str] = mapped_column(String(128), nullable=False)
    official_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    version_label: Mapped[str] = mapped_column(String(128), nullable=False)
    publication_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    applicability_scope: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_status: Mapped[str] = mapped_column(String(32), nullable=False, default="UNVERIFIED", index=True)
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    verification_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_by: Mapped[str | None] = mapped_column(String(256), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class InterpretationDecision(Base):
    __tablename__ = "interpretation_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    obligation_id: Mapped[int] = mapped_column(
        ForeignKey("extracted_obligations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    interpretation: Mapped[str] = mapped_column(Text, nullable=False)
    applicability: Mapped[str] = mapped_column(String(32), nullable=False, default="UNDECIDED")
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    assumptions: Mapped[str] = mapped_column(Text, nullable=False, default="")
    unresolved_questions: Mapped[str] = mapped_column(Text, nullable=False, default="")
    decision_owner: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT", index=True)
    submitted_by: Mapped[str] = mapped_column(String(256), nullable=False)
    reviewed_by: Mapped[str | None] = mapped_column(String(256), nullable=True)
    reviewer_role: Mapped[str | None] = mapped_column(String(128), nullable=True)
    review_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    supersedes_id: Mapped[int | None] = mapped_column(
        ForeignKey("interpretation_decisions.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
