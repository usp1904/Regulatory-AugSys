"""CTD section taxonomy node."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CtdSection(Base):
    __tablename__ = "ctd_sections"
    __table_args__ = (UniqueConstraint("code", name="uq_ctd_sections_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("ctd_sections.id", ondelete="RESTRICT"),
        nullable=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    parent: Mapped[CtdSection | None] = relationship(
        "CtdSection",
        remote_side="CtdSection.id",
        back_populates="children",
    )
    children: Mapped[list[CtdSection]] = relationship(
        "CtdSection",
        back_populates="parent",
        order_by="CtdSection.sort_order",
    )
