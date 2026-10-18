"""Persist source-linked obligation candidates.

Revision ID: 0004_obligation_extraction
Revises: 0003_clarification_queue
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_obligation_extraction"
down_revision: str | None = "0003_clarification_queue"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "extracted_obligations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("obligation_key", sa.String(64), nullable=False),
        sa.Column("source_document_id", sa.Integer(), nullable=False),
        sa.Column("mapping_id", sa.Integer(), nullable=True),
        sa.Column("source_version", sa.Integer(), nullable=False),
        sa.Column("source_file_hash", sa.String(64), nullable=False),
        sa.Column("clause_id", sa.String(128), nullable=False),
        sa.Column("segment_index", sa.Integer(), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("trigger_terms", sa.String(512), nullable=False),
        sa.Column("extraction_method", sa.String(64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("reviewer", sa.String(256), nullable=True),
        sa.Column("review_rationale", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["source_document_id"], ["documents.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["mapping_id"], ["requirements_mappings.id"], ondelete="SET NULL"
        ),
        sa.UniqueConstraint("obligation_key", name="uq_extracted_obligations_key"),
        sa.UniqueConstraint(
            "source_document_id",
            "source_version",
            "clause_id",
            name="uq_extracted_obligation_source_clause_version",
        ),
    )
    op.create_index(
        "ix_extracted_obligations_source_document_id",
        "extracted_obligations",
        ["source_document_id"],
    )
    op.create_index(
        "ix_extracted_obligations_mapping_id", "extracted_obligations", ["mapping_id"]
    )
    op.create_index("ix_extracted_obligations_status", "extracted_obligations", ["status"])


def downgrade() -> None:
    op.drop_index(
        "ix_extracted_obligations_status", table_name="extracted_obligations"
    )
    op.drop_index(
        "ix_extracted_obligations_mapping_id", table_name="extracted_obligations"
    )
    op.drop_index(
        "ix_extracted_obligations_source_document_id",
        table_name="extracted_obligations",
    )
    op.drop_table("extracted_obligations")
