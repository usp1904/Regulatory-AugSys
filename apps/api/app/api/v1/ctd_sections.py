"""CTD section API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.ctd_section import CtdSection
from app.schemas.ctd_section import CtdSectionTreeResponse
from app.services.ctd_tree import build_ctd_tree

router = APIRouter(prefix="/ctd-sections", tags=["ctd-sections"])


@router.get("", response_model=CtdSectionTreeResponse)
def list_ctd_sections(db: Session = Depends(get_db)) -> CtdSectionTreeResponse:
    sections = db.scalars(select(CtdSection).order_by(CtdSection.id)).all()
    return CtdSectionTreeResponse(sections=build_ctd_tree(list(sections)))
