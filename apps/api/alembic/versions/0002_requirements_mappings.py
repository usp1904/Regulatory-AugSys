"""Create persistent requirements mappings.

Revision ID: 0002_requirements_mappings
Revises: 0001_initial
Create Date: 2026-10-18
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_requirements_mappings"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "requirements_mappings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("mapping_key", sa.String(length=64), nullable=False),
        sa.Column("dossier_id", sa.String(length=128), nullable=False),
        sa.Column("data_json", sa.Text(), nullable=False),
        sa.Column("readiness_status", sa.String(length=40), nullable=False),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("created_by", sa.String(length=256), nullable=False),
        sa.Column("reviewer", sa.String(length=256), nullable=True),
        sa.Column(\n            "reviewer_decision", sa.String(length=32), nullable=True\n        ),
        sa.Column(\n            "reviewer_rationale", sa.Text(), nullable=True\n        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(\n            "mapping_key",\n        ),
    )
    op.create_index(\n        "ix_requirements_mappings_mapping_key", "requirements_mappings", ["mapping_key"]\n    )
    op.create_index(\n        "ix_requirements_mappings_dossier_id", "requirements_mappings", ["dossier_id"]\n    )
    op.create_index(\n        "ix_requirements_mappings_readiness_status", "requirements_mappings", ["readiness_status"]\n    )
    op.create_index(\n        "ix_requirements_mappings_review_status", "requirements_mappings", ["review_status"]\n    )


def downgrade() -> None:
    op.drop_index("ix_requirements_mappings_review_status", table_name="requirements_mappings")
    op.drop_index("ix_requirements_mappings_readiness_status", table_name="requirements_mappings")
    op.drop_index("ix_requirements_mappings_dossier_id", table_name="requirements_mappings")
    op.drop_index("ix_requirements_mappings_mapping_key", table_name="requirements_mappings")
    op.drop_table("requirements_mappings")
