"""Shared evidence query helpers (Supermemory: single source for approved lists)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.evidence_item import EvidenceItem
from app.services.ctd_ordering import ctd_code_sort_key


def list_approved_evidence_for_dossier(
    db: Session,
    dossier_id: str,
    *,
    load_source: bool = False,
) -> list[EvidenceItem]:
    """Return APPROVED evidence for a dossier, sorted by CTD numeric order."""
    query = (
        select(EvidenceItem)
        .where(EvidenceItem.dossier_id == dossier_id)
        .where(EvidenceItem.review_status == "APPROVED")
    )
    if load_source:
        query = query.options(joinedload(EvidenceItem.source_document))
    items = list(db.scalars(query).all())
    items.sort(key=lambda item: (ctd_code_sort_key(item.ctd_section_code), item.id))
    return items
