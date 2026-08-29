"""Add evidence items and audit evidence linkage.

Revision ID: 0005_evidence_items
Revises: 0004_controlled_ingestion
Create Date: 2026-08-29

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_evidence_items"
down_revision: str | None = "0004_controlled_ingestion"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "evidence_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("evidence_key", sa.String(length=64), nullable=False),
        sa.Column("evidence_version", sa.Integer(), nullable=False),
        sa.Column("dossier_id", sa.String(length=128), nullable=False),
        sa.Column("ctd_section_code", sa.String(length=32), nullable=True),
        sa.Column("source_document_id", sa.Integer(), nullable=True),
        sa.Column("source_document_version", sa.Integer(), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("paragraph_index", sa.Integer(), nullable=True),
        sa.Column("exact_source_excerpt", sa.Text(), nullable=False),
        sa.Column("normalized_summary", sa.Text(), nullable=True),
        sa.Column("evidence_type", sa.String(length=32), nullable=False),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("reviewer", sa.String(length=256), nullable=True),
        sa.Column("reviewer_decision", sa.String(length=32), nullable=True),
        sa.Column("reviewer_rationale", sa.Text(), nullable=True),
        sa.Column("supersedes_id", sa.Integer(), nullable=True),
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
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["source_document_id"], ["documents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["supersedes_id"], ["evidence_items.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evidence_items_evidence_key", "evidence_items", ["evidence_key"])
    op.create_index("ix_evidence_items_dossier_id", "evidence_items", ["dossier_id"])
    op.create_index("ix_evidence_items_ctd_section_code", "evidence_items", ["ctd_section_code"])
    op.create_index(
        "ix_evidence_items_source_document_id",
        "evidence_items",
        ["source_document_id"],
    )
    op.create_index("ix_evidence_items_review_status", "evidence_items", ["review_status"])

    with op.batch_alter_table("audit_events") as batch_op:
        batch_op.add_column(sa.Column("evidence_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_audit_events_evidence_id",
            "evidence_items",
            ["evidence_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_audit_events_evidence_id", ["evidence_id"])


def downgrade() -> None:
    with op.batch_alter_table("audit_events") as batch_op:
        batch_op.drop_index("ix_audit_events_evidence_id")
        batch_op.drop_constraint("fk_audit_events_evidence_id", type_="foreignkey")
        batch_op.drop_column("evidence_id")
    op.drop_index("ix_evidence_items_review_status", table_name="evidence_items")
    op.drop_index("ix_evidence_items_source_document_id", table_name="evidence_items")
    op.drop_index("ix_evidence_items_ctd_section_code", table_name="evidence_items")
    op.drop_index("ix_evidence_items_dossier_id", table_name="evidence_items")
    op.drop_index("ix_evidence_items_evidence_key", table_name="evidence_items")
    op.drop_table("evidence_items")
