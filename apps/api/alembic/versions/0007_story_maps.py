"""Add Story Map workspace tables.

Revision ID: 0007_story_maps
Revises: 0006_dossier_exports
Create Date: 2026-09-03

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007_story_maps"
down_revision: str | None = "0006_dossier_exports"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "story_maps",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("map_key", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("template", sa.String(length=64), nullable=False),
        sa.Column("intent", sa.Text(), nullable=False),
        sa.Column("group_by", sa.String(length=32), nullable=False),
        sa.Column("package_status", sa.String(length=32), nullable=False),
        sa.Column("created_by", sa.String(length=256), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("map_key", name="uq_story_maps_map_key"),
    )
    op.create_index("ix_story_maps_map_key", "story_maps", ["map_key"])

    op.create_table(
        "story_map_backbones",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("story_map_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["story_map_id"], ["story_maps.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_story_map_backbones_story_map_id", "story_map_backbones", ["story_map_id"])

    op.create_table(
        "story_map_release_slices",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("story_map_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("release_meaning", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["story_map_id"], ["story_maps.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_story_map_release_slices_story_map_id",
        "story_map_release_slices",
        ["story_map_id"],
    )

    op.create_table(
        "story_map_stories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("story_map_id", sa.Integer(), nullable=False),
        sa.Column("backbone_id", sa.Integer(), nullable=True),
        sa.Column("release_slice_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("group_key", sa.String(length=256), nullable=True),
        sa.Column("owner", sa.String(length=256), nullable=True),
        sa.Column("outcome_or_obligation", sa.Text(), nullable=True),
        sa.Column("acceptance_criteria", sa.Text(), nullable=True),
        sa.Column("evidence_required", sa.Text(), nullable=True),
        sa.Column("risk", sa.Text(), nullable=True),
        sa.Column("dependency", sa.Text(), nullable=True),
        sa.Column("source_control_ref", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["backbone_id"], ["story_map_backbones.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["release_slice_id"],
            ["story_map_release_slices.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["story_map_id"], ["story_maps.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_story_map_stories_story_map_id", "story_map_stories", ["story_map_id"])
    op.create_index("ix_story_map_stories_backbone_id", "story_map_stories", ["backbone_id"])
    op.create_index(
        "ix_story_map_stories_release_slice_id",
        "story_map_stories",
        ["release_slice_id"],
    )

    op.create_table(
        "story_map_trace_links",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("story_id", sa.Integer(), nullable=False),
        sa.Column("link_type", sa.String(length=64), nullable=False),
        sa.Column("external_ref", sa.String(length=512), nullable=False),
        sa.Column("label", sa.String(length=512), nullable=False),
        sa.Column("source_workspace", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["story_id"], ["story_map_stories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_story_map_trace_links_story_id", "story_map_trace_links", ["story_id"])


def downgrade() -> None:
    op.drop_index("ix_story_map_trace_links_story_id", table_name="story_map_trace_links")
    op.drop_table("story_map_trace_links")
    op.drop_index("ix_story_map_stories_release_slice_id", table_name="story_map_stories")
    op.drop_index("ix_story_map_stories_backbone_id", table_name="story_map_stories")
    op.drop_index("ix_story_map_stories_story_map_id", table_name="story_map_stories")
    op.drop_table("story_map_stories")
    op.drop_index("ix_story_map_release_slices_story_map_id", table_name="story_map_release_slices")
    op.drop_table("story_map_release_slices")
    op.drop_index("ix_story_map_backbones_story_map_id", table_name="story_map_backbones")
    op.drop_table("story_map_backbones")
    op.drop_index("ix_story_maps_map_key", table_name="story_maps")
    op.drop_table("story_maps")
