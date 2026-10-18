"""Add clarification queue and append-only decision history.

Revision ID: 0003_clarification_queue
Revises: 0002_requirements_mappings
Create Date: 2026-10-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_clarification_queue"
down_revision: str | None = "0002_requirements_mappings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "clarification_questions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("question_key", sa.String(length=64), nullable=False),
        sa.Column("mapping_id", sa.Integer(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("owner", sa.String(length=256), nullable=False),
        sa.Column("created_by", sa.String(length=256), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("answered_by", sa.String(length=256), nullable=True),
        sa.Column("decision", sa.Text(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("resolved_by", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["mapping_id"], ["requirements_mappings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("question_key"),
    )
    op.create_index("ix_clarification_questions_question_key", "clarification_questions", ["question_key"])
    op.create_index("ix_clarification_questions_mapping_id", "clarification_questions", ["mapping_id"])
    op.create_index("ix_clarification_questions_status", "clarification_questions", ["status"])

    op.create_table(
        "clarification_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("clarification_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("actor", sa.String(length=256), nullable=False),
        sa.Column("snapshot_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["clarification_id"], ["clarification_questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_clarification_history_clarification_id", "clarification_history", ["clarification_id"])


def downgrade() -> None:
    op.drop_index("ix_clarification_history_clarification_id", table_name="clarification_history")
    op.drop_table("clarification_history")
    op.drop_index("ix_clarification_questions_status", table_name="clarification_questions")
    op.drop_index("ix_clarification_questions_mapping_id", table_name="clarification_questions")
    op.drop_index("ix_clarification_questions_question_key", table_name="clarification_questions")
    op.drop_table("clarification_questions")
