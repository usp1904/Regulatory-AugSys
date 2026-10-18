"""Add controlled regulatory source registry and interpretation decisions.

Revision ID: 0005_regulatory_truth_and_interpretation
Revises: 0004_obligation_extraction
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_regulatory_truth_and_interpretation"
down_revision: str | None = "0004_obligation_extraction"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "regulatory_sources",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_key", sa.String(64), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("document_version", sa.Integer(), nullable=False),
        sa.Column("file_hash", sa.String(64), nullable=False),
        sa.Column("authority", sa.String(256), nullable=False),
        sa.Column("jurisdiction", sa.String(128), nullable=False),
        sa.Column("source_type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("official_url", sa.String(2048), nullable=False),
        sa.Column("source_version_label", sa.String(128), nullable=False),
        sa.Column("publication_date", sa.Date(), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("review_due_date", sa.Date(), nullable=True),
        sa.Column("clause_id", sa.String(128), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("source_status", sa.String(32), nullable=False),
        sa.Column("currentness_status", sa.String(32), nullable=False),
        sa.Column("created_by", sa.String(256), nullable=False),
        sa.Column("reviewer", sa.String(256), nullable=True),
        sa.Column("review_rationale", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("source_key", name="uq_regulatory_sources_source_key"),
        sa.UniqueConstraint("document_id", "document_version", "clause_id", name="uq_regulatory_source_document_version_clause"),
    )
    op.create_index("ix_regulatory_sources_source_key", "regulatory_sources", ["source_key"], unique=True)
    op.create_index("ix_regulatory_sources_document_id", "regulatory_sources", ["document_id"])
    op.create_index("ix_regulatory_sources_source_status", "regulatory_sources", ["source_status"])

    op.create_table(
        "approved_interpretations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("interpretation_key", sa.String(64), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("obligation_id", sa.Integer(), nullable=True),
        sa.Column("interpretation", sa.Text(), nullable=False),
        sa.Column("applicability", sa.String(32), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("decision_owner", sa.String(256), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_by", sa.String(256), nullable=False),
        sa.Column("reviewer", sa.String(256), nullable=True),
        sa.Column("review_rationale", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["regulatory_sources.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["obligation_id"], ["extracted_obligations.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("interpretation_key", name="uq_approved_interpretations_key"),
    )
    op.create_index("ix_approved_interpretations_interpretation_key", "approved_interpretations", ["interpretation_key"], unique=True)
    op.create_index("ix_approved_interpretations_source_id", "approved_interpretations", ["source_id"])
    op.create_index("ix_approved_interpretations_obligation_id", "approved_interpretations", ["obligation_id"])
    op.create_index("ix_approved_interpretations_status", "approved_interpretations", ["status"])


def downgrade() -> None:
    op.drop_index("ix_approved_interpretations_status", table_name="approved_interpretations")
    op.drop_index("ix_approved_interpretations_obligation_id", table_name="approved_interpretations")
    op.drop_index("ix_approved_interpretations_source_id", table_name="approved_interpretations")
    op.drop_index("ix_approved_interpretations_interpretation_key", table_name="approved_interpretations")
    op.drop_table("approved_interpretations")
    op.drop_index("ix_regulatory_sources_source_status", table_name="regulatory_sources")
    op.drop_index("ix_regulatory_sources_document_id", table_name="regulatory_sources")
    op.drop_index("ix_regulatory_sources_source_key", table_name="regulatory_sources")
    op.drop_table("regulatory_sources")
