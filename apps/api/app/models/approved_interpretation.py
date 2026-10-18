"""Organisation-specific interpretation kept separate from source text."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ApprovedInterpretation(Base):
    __tablename__ = "approved_interpretations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interpretation_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("regulatory_sources.id", ondelete="RESTRICT"), nullable=False, index=True)
    obligation_id: Mapped[int | None] = mapped_column(ForeignKey("extracted_obligations.id", ondelete="SET NULL"), nullable=True, index=True)
    interpretation: Mapped[str] = mapped_column(Text, nullable=False)
    applicability: Mapped[str] = mapped_column(String(32), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    decision_owner: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT", index=True)
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    reviewer: Mapped[str | None] = mapped_column(String(256), nullable=True)
    review_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
