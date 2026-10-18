"""Create persistent extracted obligation candidates.

Revision ID: 0003_obligation_extraction
Revises: 0002_requirements_mappings
Create Date: 2026-10-18
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_obligation_extraction"
down_revision: str | None = "0002_requirements_mappings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "extracted_obligations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("obligation_key", sa.String(length=64), nullable=False),
        sa.Column("source_document_id", sa.Integer(), nullable=False),
        sa.Column("source_version", sa.Integer(), nullable=False),
        sa.Column("source_file_hash", sa.String(length=64), nullable=False),
        sa.Column("clause_id", sa.String(length=128), nullable=False),
        sa.Column("segment_index", sa.Integer(), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("trigger_terms", sa.String(length=512), nullable=False),
        sa.Column("extraction_method", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("reviewer", sa.String(length=256), nullable=True),
        sa.Column("review_rationale", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["source_document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_document_id",
            "source_version",
            "clause_id",
            name="uq_extracted_obligation_source_clause_version",
        ),
    )
    op.create_index("ix_extracted_obligations_obligation_key", "extracted_obligations", ["obligation_key"], unique=True)
    op.create_index("ix_extracted_obligations_source_document_id", "extracted_obligations", ["source_document_id"])
    op.create_index("ix_extracted_obligations_status", "extracted_obligations", ["status"])


def downgrade() -> None:
    op.drop_index("ix_extracted_obligations_status", table_name="extracted_obligations")
    op.drop_index("ix_extracted_obligations_source_document_id", table_name="extracted_obligations")
    op.drop_index("ix_extracted_obligations_obligation_key", table_name="extracted_obligations")
    op.drop_table("extracted_obligations")
