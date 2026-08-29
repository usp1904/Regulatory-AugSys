"""Add CTD sections table and seed Module 3.2.S taxonomy.

Revision ID: 0002_ctd_sections
Revises: 0001_initial
Create Date: 2026-08-29

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.data.ctd_module_32s import CTD_MODULE_32S_SEED

revision: str = "0002_ctd_sections"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ctd_sections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["ctd_sections.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_ctd_sections_code"),
    )

    conn = op.get_bind()
    code_to_id: dict[str, int] = {}
    for row in CTD_MODULE_32S_SEED:
        parent_id = code_to_id.get(row["parent_code"]) if row["parent_code"] else None
        conn.execute(
            sa.text(
                "INSERT INTO ctd_sections (code, title, parent_id, sort_order) "
                "VALUES (:code, :title, :parent_id, :sort_order)"
            ),
            {
                "code": row["code"],
                "title": row["title"],
                "parent_id": parent_id,
                "sort_order": row["sort_order"],
            },
        )
        inserted = conn.execute(
            sa.text("SELECT id FROM ctd_sections WHERE code = :code"),
            {"code": row["code"]},
        )
        code_to_id[row["code"]] = inserted.scalar_one()


def downgrade() -> None:
    op.drop_table("ctd_sections")
