"""Story Map workspace ORM models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

STORY_MAP_TEMPLATES = frozenset(
    {
        "regulatory_compliance",
        "business_process",
        "outcome_oriented",
        "classic_user_journey",
        "feature_breakdown",
        "role_based",
        "component_technical_module",
        "customer_value_stream",
        "legacy_preservation",
        "enterprise_migration",
        "pi_planning",
    }
)

RELEASE_MEANINGS = frozenset(
    {
        "regulatory_deadline",
        "mvp_value_increment",
        "moscow_priority",
        "migration_wave",
        "technical_dependency",
        "pi_objective",
        "outcome_increment",
    }
)

STORY_STATUSES = frozenset({"planned", "deferred", "blocked", "completed"})

GROUP_BY_OPTIONS = frozenset({"persona", "process", "outcome", "feature", "technical_module"})

TRACE_LINK_TYPES = frozenset(
    {
        "regulation_control",
        "sop_policy",
        "gap_inspection_item",
        "comparison_difference",
        "ctd_section",
        "pbi_evidence_request",
    }
)

TRACE_SOURCE_WORKSPACES = frozenset(
    {
        "assure",
        "sop_mapper",
        "inspection_readiness",
        "validation_gaps",
        "global_compare",
        "ctd_ectd",
        "evidence",
    }
)

if TYPE_CHECKING:
    pass


class StoryMap(Base):
    __tablename__ = "story_maps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    map_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    template: Mapped[str] = mapped_column(String(64), nullable=False)
    intent: Mapped[str] = mapped_column(Text, nullable=False, default="")
    group_by: Mapped[str] = mapped_column(String(32), nullable=False, default="outcome")
    package_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="DRAFT_NOT_CONTROLLED"
    )
    created_by: Mapped[str] = mapped_column(String(256), nullable=False, default="unknown")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    backbones: Mapped[list[StoryMapBackbone]] = relationship(
        "StoryMapBackbone",
        back_populates="story_map",
        cascade="all, delete-orphan",
        order_by="StoryMapBackbone.sort_order",
    )
    release_slices: Mapped[list[StoryMapReleaseSlice]] = relationship(
        "StoryMapReleaseSlice",
        back_populates="story_map",
        cascade="all, delete-orphan",
        order_by="StoryMapReleaseSlice.sort_order",
    )
    stories: Mapped[list[StoryMapStory]] = relationship(
        "StoryMapStory",
        back_populates="story_map",
        cascade="all, delete-orphan",
        order_by="StoryMapStory.sort_order",
    )

    @staticmethod
    def new_map_key() -> str:
        return f"SM-{uuid4().hex[:16].upper()}"


class StoryMapBackbone(Base):
    __tablename__ = "story_map_backbones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    story_map_id: Mapped[int] = mapped_column(
        ForeignKey("story_maps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    story_map: Mapped[StoryMap] = relationship("StoryMap", back_populates="backbones")
    stories: Mapped[list[StoryMapStory]] = relationship(
        "StoryMapStory",
        back_populates="backbone",
        order_by="StoryMapStory.sort_order",
    )


class StoryMapReleaseSlice(Base):
    __tablename__ = "story_map_release_slices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    story_map_id: Mapped[int] = mapped_column(
        ForeignKey("story_maps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    release_meaning: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    story_map: Mapped[StoryMap] = relationship("StoryMap", back_populates="release_slices")
    stories: Mapped[list[StoryMapStory]] = relationship(
        "StoryMapStory",
        back_populates="release_slice",
    )


class StoryMapStory(Base):
    __tablename__ = "story_map_stories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    story_map_id: Mapped[int] = mapped_column(
        ForeignKey("story_maps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    backbone_id: Mapped[int | None] = mapped_column(
        ForeignKey("story_map_backbones.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    release_slice_id: Mapped[int | None] = mapped_column(
        ForeignKey("story_map_release_slices.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    group_key: Mapped[str | None] = mapped_column(String(256), nullable=True)
    owner: Mapped[str | None] = mapped_column(String(256), nullable=True)
    outcome_or_obligation: Mapped[str | None] = mapped_column(Text, nullable=True)
    acceptance_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_required: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk: Mapped[str | None] = mapped_column(Text, nullable=True)
    dependency: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_control_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="planned")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    story_map: Mapped[StoryMap] = relationship("StoryMap", back_populates="stories")
    backbone: Mapped[StoryMapBackbone | None] = relationship(
        "StoryMapBackbone",
        back_populates="stories",
    )
    release_slice: Mapped[StoryMapReleaseSlice | None] = relationship(
        "StoryMapReleaseSlice",
        back_populates="stories",
    )
    trace_links: Mapped[list[StoryMapTraceLink]] = relationship(
        "StoryMapTraceLink",
        back_populates="story",
        cascade="all, delete-orphan",
    )


class StoryMapTraceLink(Base):
    __tablename__ = "story_map_trace_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    story_id: Mapped[int] = mapped_column(
        ForeignKey("story_map_stories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    link_type: Mapped[str] = mapped_column(String(64), nullable=False)
    external_ref: Mapped[str] = mapped_column(String(512), nullable=False)
    label: Mapped[str] = mapped_column(String(512), nullable=False)
    source_workspace: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    story: Mapped[StoryMapStory] = relationship("StoryMapStory", back_populates="trace_links")
