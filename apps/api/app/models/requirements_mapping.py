"""Persistent draft requirements mappings and review status."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RequirementsMapping(Base):
    __tablename__ = "requirements_mappings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    mapping_key: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        default=lambda: f"MAP-{uuid4().hex.upper()}",
    )
    dossier_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
    )
    data_json: Mapped[str] = mapped_column(Text, nullable=False)
    readiness_status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="BLOCKED_DRAFT",
        index=True,
    )
    review_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="PENDING",
        index=True,
    )
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    reviewer: Mapped[str | None] = mapped_column(String(256), nullable=True)
    reviewer_decision: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reviewer_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
