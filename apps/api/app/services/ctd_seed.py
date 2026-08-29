"""Seed CTD Module 3.2.S taxonomy into the database."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.ctd_module_32s import CTD_MODULE_32S_SEED
from app.models.ctd_section import CtdSection


def seed_ctd_module_32s(db: Session) -> None:
    existing = db.scalar(select(CtdSection.id).limit(1))
    if existing is not None:
        return

    code_to_id: dict[str, int] = {}
    for row in CTD_MODULE_32S_SEED:
        parent_id = None
        if row["parent_code"] is not None:
            parent_id = code_to_id[row["parent_code"]]
        section = CtdSection(
            code=row["code"],
            title=row["title"],
            parent_id=parent_id,
            sort_order=row["sort_order"],
        )
        db.add(section)
        db.flush()
        code_to_id[row["code"]] = section.id

    db.commit()
