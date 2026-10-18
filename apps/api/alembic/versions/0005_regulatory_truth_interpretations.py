"""Add regulatory source truth and organisational interpretation records.

Revision ID: 0005_regulatory_truth_interpretations
Revises: 0004_obligation_extraction
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_regulatory_truth_interpretations"
down_revision: str | None = "0004_obligation_extraction"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "regulatory_source_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("issuing_authority", sa.String(256), nullable=False),
        sa.Column("jurisdiction", sa.String(256), nullable=False),
        sa.Column("document_type", sa.String(128), nullable=False),
        sa.Column("official_url", sa.String(2048), nullable=False),
        sa.Column("version_label", sa.String(128), nullable=False),
        sa.Column("publication_date", sa.Date(), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("applicability_scope", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column(
            "source_status", sa.String(32), nullable=False, server_default="UNVERIFIED"
        ),
        sa.Column("created_by", sa.String(256), nullable=False),
        sa.Column("verification_rationale", sa.Text(), nullable=True),
        sa.Column("verified_by", sa.String(256), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("document_id", name="uq_regulatory_source_document"),
    )
    op.create_index(
        "ix_regulatory_source_records_document_id",
        "regulatory_source_records",
        ["document_id"],
    )
    op.create_index(
        "ix_regulatory_source_records_source_status",
        "regulatory_source_records",
        ["source_status"],
    )

    op.create_table(
        "interpretation_decisions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("obligation_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("interpretation", sa.Text(), nullable=False),
        sa.Column(
            "applicability", sa.String(32), nullable=False, server_default="UNDECIDED"
        ),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("assumptions", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "unresolved_questions", sa.Text(), nullable=False, server_default=""
        ),
        sa.Column("decision_owner", sa.String(256), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("submitted_by", sa.String(256), nullable=False),
        sa.Column("reviewed_by", sa.String(256), nullable=True),
        sa.Column("reviewer_role", sa.String(128), nullable=True),
        sa.Column("review_rationale", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("supersedes_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["obligation_id"], ["extracted_obligations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["supersedes_id"], ["interpretation_decisions.id"], ondelete="SET NULL"
        ),
    )
    op.create_index(
        "ix_interpretation_decisions_obligation_id",
        "interpretation_decisions",
        ["obligation_id"],
    )
    op.create_index("ix_interpretation_decisions_status", "interpretation_decisions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_interpretation_decisions_status", table_name="interpretation_decisions")
    op.drop_index(
        "ix_interpretation_decisions_obligation_id",
        table_name="interpretation_decisions",
    )
    op.drop_table("interpretation_decisions")
    op.drop_index(
        "ix_regulatory_source_records_source_status",
        table_name="regulatory_source_records",
    )
    op.drop_index(
        "ix_regulatory_source_records_document_id",
        table_name="regulatory_source_records",
    )
    op.drop_table("regulatory_source_records")
