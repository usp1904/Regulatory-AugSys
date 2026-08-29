"""Evidence capture, versioning, review, and export rules."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.evidence_item import (
    GAP_EXPORT_TYPES,
    REVIEW_STATUSES,
    EvidenceItem,
)
from app.schemas.evidence import (
    EvidenceCreateRequest,
    EvidenceExportItem,
    EvidenceExportResponse,
    EvidenceResponse,
    EvidenceReviewRequest,
    EvidenceUpdateRequest,
)
from app.services.audit import record_audit_event
from app.services.ctd_ordering import ctd_code_sort_key


class EvidenceServiceError(ValueError):
    """Business rule violation for evidence workflow."""


def _to_response(item: EvidenceItem) -> EvidenceResponse:
    return EvidenceResponse(
        id=item.id,
        evidence_key=item.evidence_key,
        evidence_version=item.evidence_version,
        dossier_id=item.dossier_id,
        ctd_section_code=item.ctd_section_code,
        source_document_id=item.source_document_id,
        source_document_version=item.source_document_version,
        page_number=item.page_number,
        paragraph_index=item.paragraph_index,
        exact_source_excerpt=item.exact_source_excerpt,
        normalized_summary=item.normalized_summary,
        evidence_type=item.evidence_type,
        review_status=item.review_status,
        reviewer=item.reviewer,
        reviewer_decision=item.reviewer_decision,
        reviewer_rationale=item.reviewer_rationale,
        supersedes_id=item.supersedes_id,
        created_by=item.created_by,
        created_at=item.created_at,
        updated_at=item.updated_at,
        reviewed_at=item.reviewed_at,
        excerpt_locked=item.review_status == "APPROVED",
    )


def _validate_source_document(db: Session, payload: EvidenceCreateRequest) -> Document | None:
    if payload.evidence_type == "GAP":
        return None
    if payload.source_document_id is None:
        raise EvidenceServiceError("source_document_id is required unless evidence_type is GAP")
    document = db.get(Document, payload.source_document_id)
    if document is None:
        raise EvidenceServiceError("source document not found")
    return document


def create_evidence(db: Session, payload: EvidenceCreateRequest) -> EvidenceItem:
    document = _validate_source_document(db, payload)
    if payload.evidence_type != "GAP" and not payload.exact_source_excerpt.strip():
        raise EvidenceServiceError("exact_source_excerpt is required")

    item = EvidenceItem(
        evidence_key=EvidenceItem.new_evidence_key(),
        evidence_version=1,
        dossier_id=payload.dossier_id,
        ctd_section_code=payload.ctd_section_code,
        source_document_id=document.id if document else None,
        source_document_version=document.version if document else None,
        page_number=payload.page_number,
        paragraph_index=payload.paragraph_index,
        exact_source_excerpt=payload.exact_source_excerpt.strip(),
        normalized_summary=payload.normalized_summary,
        evidence_type=payload.evidence_type,
        review_status="PENDING",
        created_by=payload.created_by,
    )
    db.add(item)
    db.flush()
    record_audit_event(
        db,
        event_type="evidence_create",
        actor=payload.created_by,
        document_id=item.source_document_id,
        evidence_id=item.id,
        detail={
            "evidence_key": item.evidence_key,
            "dossier_id": item.dossier_id,
            "ctd_section_code": item.ctd_section_code,
            "evidence_type": item.evidence_type,
        },
    )
    db.commit()
    db.refresh(item)
    return item


def _next_version(db: Session, evidence_key: str) -> int:
    current = db.scalar(
        select(func.coalesce(func.max(EvidenceItem.evidence_version), 0)).where(
            EvidenceItem.evidence_key == evidence_key
        )
    )
    return int(current or 0) + 1


def _clone_for_new_version(
    db: Session, item: EvidenceItem, payload: EvidenceUpdateRequest
) -> EvidenceItem:
    excerpt = item.exact_source_excerpt
    if payload.exact_source_excerpt is not None:
        excerpt = payload.exact_source_excerpt.strip()
    evidence_type = payload.evidence_type or item.evidence_type
    return EvidenceItem(
        evidence_key=item.evidence_key,
        evidence_version=_next_version(db, item.evidence_key),
        dossier_id=item.dossier_id,
        ctd_section_code=payload.ctd_section_code
        if payload.ctd_section_code is not None
        else item.ctd_section_code,
        source_document_id=item.source_document_id,
        source_document_version=item.source_document_version,
        page_number=item.page_number,
        paragraph_index=item.paragraph_index,
        exact_source_excerpt=excerpt,
        normalized_summary=payload.normalized_summary
        if payload.normalized_summary is not None
        else item.normalized_summary,
        evidence_type=evidence_type,
        review_status="PENDING",
        supersedes_id=item.id,
        created_by=payload.actor,
    )


def update_evidence(
    db: Session, item: EvidenceItem, payload: EvidenceUpdateRequest
) -> EvidenceItem:
    if item.review_status == "APPROVED":
        if payload.exact_source_excerpt is not None and (
            payload.exact_source_excerpt.strip() != item.exact_source_excerpt
        ):
            new_item = _clone_for_new_version(db, item, payload)
            db.add(new_item)
            db.flush()
            record_audit_event(
                db,
                event_type="evidence_version_create",
                actor=payload.actor,
                document_id=new_item.source_document_id,
                evidence_id=new_item.id,
                detail={
                    "evidence_key": new_item.evidence_key,
                    "supersedes_id": item.id,
                    "reason": "approved excerpt change",
                },
            )
            db.commit()
            db.refresh(new_item)
            return new_item

        changed = False
        if (
            payload.ctd_section_code is not None
            and payload.ctd_section_code != item.ctd_section_code
        ):
            changed = True
        if (
            payload.normalized_summary is not None
            and payload.normalized_summary != item.normalized_summary
        ):
            changed = True
        if payload.evidence_type is not None and payload.evidence_type != item.evidence_type:
            changed = True
        if changed:
            new_item = _clone_for_new_version(db, item, payload)
            new_item.exact_source_excerpt = item.exact_source_excerpt
            db.add(new_item)
            db.flush()
            record_audit_event(
                db,
                event_type="evidence_version_create",
                actor=payload.actor,
                document_id=new_item.source_document_id,
                evidence_id=new_item.id,
                detail={
                    "evidence_key": new_item.evidence_key,
                    "supersedes_id": item.id,
                    "reason": "approved metadata change",
                },
            )
            db.commit()
            db.refresh(new_item)
            return new_item

        raise EvidenceServiceError("No mutable fields changed on approved evidence")

    if payload.exact_source_excerpt is not None:
        item.exact_source_excerpt = payload.exact_source_excerpt.strip()
    if payload.normalized_summary is not None:
        item.normalized_summary = payload.normalized_summary
    if payload.ctd_section_code is not None:
        item.ctd_section_code = payload.ctd_section_code
    if payload.evidence_type is not None:
        item.evidence_type = payload.evidence_type
    item.updated_at = datetime.now(UTC)
    record_audit_event(
        db,
        event_type="evidence_update",
        actor=payload.actor,
        document_id=item.source_document_id,
        evidence_id=item.id,
        detail={"evidence_key": item.evidence_key, "review_status": item.review_status},
    )
    db.commit()
    db.refresh(item)
    return item


def review_evidence(
    db: Session, item: EvidenceItem, payload: EvidenceReviewRequest
) -> EvidenceItem:
    if item.review_status == "APPROVED" and payload.decision != "APPROVED":
        raise EvidenceServiceError("Approved evidence cannot be re-reviewed without a new version")

    item.reviewer = payload.reviewer
    item.reviewer_decision = payload.decision
    item.reviewer_rationale = payload.rationale
    item.review_status = payload.decision
    item.reviewed_at = datetime.now(UTC)
    item.updated_at = datetime.now(UTC)
    record_audit_event(
        db,
        event_type="evidence_review",
        actor=payload.reviewer,
        document_id=item.source_document_id,
        evidence_id=item.id,
        detail={
            "decision": payload.decision,
            "rationale": payload.rationale,
            "evidence_key": item.evidence_key,
        },
    )
    db.commit()
    db.refresh(item)
    return item


def list_evidence(
    db: Session,
    *,
    dossier_id: str | None = None,
    ctd_section_code: str | None = None,
    review_status: str | None = None,
) -> list[EvidenceItem]:
    query = select(EvidenceItem).order_by(EvidenceItem.id.desc())
    if dossier_id:
        query = query.where(EvidenceItem.dossier_id == dossier_id)
    if ctd_section_code:
        query = query.where(EvidenceItem.ctd_section_code == ctd_section_code)
    if review_status:
        if review_status not in REVIEW_STATUSES:
            raise EvidenceServiceError(f"Invalid review_status: {review_status}")
        query = query.where(EvidenceItem.review_status == review_status)
    return list(db.scalars(query).all())


def export_approved_evidence(db: Session, dossier_id: str) -> EvidenceExportResponse:
    items = list(
        db.scalars(
            select(EvidenceItem)
            .where(EvidenceItem.dossier_id == dossier_id)
            .where(EvidenceItem.review_status == "APPROVED")
        ).all()
    )
    items.sort(key=lambda item: (ctd_code_sort_key(item.ctd_section_code), item.id))
    export_items: list[EvidenceExportItem] = []
    for item in items:
        if item.evidence_type in GAP_EXPORT_TYPES:
            export_items.append(
                EvidenceExportItem(
                    evidence_key=item.evidence_key,
                    evidence_version=item.evidence_version,
                    dossier_id=item.dossier_id,
                    ctd_section_code=item.ctd_section_code,
                    evidence_type=item.evidence_type,
                    export_label="CONTROLLED_GAP_STATEMENT",
                    normalized_summary=item.normalized_summary or item.exact_source_excerpt,
                    reviewer=item.reviewer,
                    reviewed_at=item.reviewed_at,
                )
            )
        else:
            export_items.append(
                EvidenceExportItem(
                    evidence_key=item.evidence_key,
                    evidence_version=item.evidence_version,
                    dossier_id=item.dossier_id,
                    ctd_section_code=item.ctd_section_code,
                    evidence_type=item.evidence_type,
                    export_label="APPROVED_EVIDENCE",
                    exact_source_excerpt=item.exact_source_excerpt,
                    normalized_summary=item.normalized_summary,
                    source_document_id=item.source_document_id,
                    source_document_version=item.source_document_version,
                    page_number=item.page_number,
                    reviewer=item.reviewer,
                    reviewed_at=item.reviewed_at,
                )
            )
    return EvidenceExportResponse(dossier_id=dossier_id, items=export_items)


def evidence_to_response(item: EvidenceItem) -> EvidenceResponse:
    return _to_response(item)
