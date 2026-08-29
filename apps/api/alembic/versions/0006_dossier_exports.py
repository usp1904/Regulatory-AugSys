"""Add dossier export immutable file records.

Revision ID: 0006_dossier_exports
Revises: 0005_evidence_items
Create Date: 2026-08-29

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_dossier_exports"
down_revision: str | None = "0005_evidence_items"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "dossier_exports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("export_id", sa.String(length=64), nullable=False),
        sa.Column("dossier_id", sa.String(length=128), nullable=False),
        sa.Column("dossier_version", sa.Integer(), nullable=False),
        sa.Column("export_format", sa.String(length=8), nullable=False),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("manifest_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(length=256), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("export_id", name="uq_dossier_exports_export_id"),
    )
    op.create_index("ix_dossier_exports_export_id", "dossier_exports", ["export_id"])
    op.create_index("ix_dossier_exports_dossier_id", "dossier_exports", ["dossier_id"])
    op.create_index("ix_dossier_exports_file_hash", "dossier_exports", ["file_hash"])


def downgrade() -> None:
    op.drop_index("ix_dossier_exports_file_hash", table_name="dossier_exports")
    op.drop_index("ix_dossier_exports_dossier_id", table_name="dossier_exports")
    op.drop_index("ix_dossier_exports_export_id", table_name="dossier_exports")
    op.drop_table("dossier_exports")
