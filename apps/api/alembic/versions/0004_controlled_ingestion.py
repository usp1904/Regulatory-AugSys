"""Controlled document ingestion schema expansion.

Revision ID: 0004_controlled_ingestion
Revises: 0003_documents
Create Date: 2026-08-29

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_controlled_ingestion"
down_revision: str | None = "0003_documents"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("documents") as batch_op:
        batch_op.add_column(
            sa.Column("byte_size", sa.Integer(), nullable=False, server_default="0")
        )
        batch_op.add_column(
            sa.Column("version", sa.Integer(), nullable=False, server_default="1")
        )
        batch_op.add_column(
            sa.Column("uploader", sa.String(length=256), nullable=False, server_default="unknown")
        )
        batch_op.add_column(sa.Column("extraction_error", sa.Text(), nullable=True))

    op.create_table(
        "document_pages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("text_content", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_document_pages_document_id", "document_pages", ["document_id"])

    op.create_table(
        "document_paragraphs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("paragraph_index", sa.Integer(), nullable=False),
        sa.Column("text_content", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_document_paragraphs_document_id", "document_paragraphs", ["document_id"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=True),
        sa.Column("actor", sa.String(length=256), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"])
    op.create_index("ix_audit_events_document_id", "audit_events", ["document_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_events_document_id", table_name="audit_events")
    op.drop_index("ix_audit_events_event_type", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_document_paragraphs_document_id", table_name="document_paragraphs")
    op.drop_table("document_paragraphs")
    op.drop_index("ix_document_pages_document_id", table_name="document_pages")
    op.drop_table("document_pages")
    with op.batch_alter_table("documents") as batch_op:
        batch_op.drop_column("extraction_error")
        batch_op.drop_column("uploader")
        batch_op.drop_column("version")
        batch_op.drop_column("byte_size")
