"""Add documents table for in-house document storage.

Revision ID: 0003_documents
Revises: 0002_ctd_sections
Create Date: 2026-08-29

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_documents"
down_revision: str | None = "0002_ctd_sections"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("parse_status", sa.String(length=32), nullable=False),
        sa.Column("text_excerpt", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_documents_file_hash", "documents", ["file_hash"])


def downgrade() -> None:
    op.drop_index("ix_documents_file_hash", table_name="documents")
    op.drop_table("documents")
