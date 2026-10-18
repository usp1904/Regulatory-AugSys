"""Persistence and approval rules for evidence layers one and two."""

import hashlib
import re
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.approved_interpretation import ApprovedInterpretation
from app.models.document import Document
from app.models.regulatory_source import RegulatorySource
from app.schemas.evidence_layers import (
    InterpretationCreate,
    InterpretationReview,
    RegulatorySourceCreate,
    RegulatorySourceReview,
)
from app.services.audit import record_audit_event


class EvidenceLayerError(ValueError):
    """An evidence-layer workflow rule was violated."""


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def create_regulatory_source(db: Session, payload: RegulatorySourceCreate) -> RegulatorySource:
    document = db.get(Document, payload.document_id)
    if document is None:
        raise EvidenceLayerError("Controlled source document not found")
    if document.parse_status != "EXTRACTED":
        raise EvidenceLayerError("Source document text extraction must be complete")
    excerpt = payload.excerpt.strip()
    if _normalize(excerpt) not in _normalize(document.full_extracted_text()):
        raise EvidenceLayerError("Clause excerpt must exactly match text in the controlled document")
    if payload.effective_date and payload.publication_date and payload.effective_date < payload.publication_date:
        raise EvidenceLayerError("Effective date cannot precede publication date")
    source = RegulatorySource(
        source_key="REG-" + uuid4().hex[:20].upper(),
        document_id=document.id,
        document_version=document.version,
        file_hash=document.file_hash,
        authority=payload.authority.strip(),
        jurisdiction=payload.jurisdiction.strip(),
        source_type=payload.source_type.strip(),
        title=payload.title.strip(),
        official_url=str(payload.official_url),
        source_version_label=payload.source_version_label.strip(),
        publication_date=payload.publication_date,
        effective_date=payload.effective_date,
        review_due_date=payload.review_due_date,
        clause_id=payload.clause_id.strip(),
        excerpt=excerpt,
        source_status="PENDING_REVIEW",
        currentness_status=payload.currentness_status,
        created_by=payload.created_by.strip(),
    )
    db.add(source)
    db.flush()
    record_audit_event(
        db, event_type="regulatory_source_registered", actor=payload.created_by,
        document_id=document.id,
        detail={"source_key": source.source_key, "document_version": document.version,
                "file_hash": document.file_hash, "clause_id": source.clause_id,
                "currentness_status": source.currentness_status},
    )
    db.commit()
    db.refresh(source)
    return source


def review_regulatory_source(
    db: Session, source: RegulatorySource, payload: RegulatorySourceReview
) -> RegulatorySource:
    if source.source_status != "PENDING_REVIEW":
        raise EvidenceLayerError("Only pending regulatory sources can be reviewed")
    document = db.get(Document, source.document_id)
    if document is None:
        raise EvidenceLayerError("Controlled source document no longer exists")
    if document.version != source.document_version or document.file_hash != source.file_hash:
        raise EvidenceLayerError("Source document version/hash changed; register and review the new version")
    if payload.decision == "APPROVED" and payload.currentness_status == "SUPERSEDED":
        raise EvidenceLayerError("A superseded source cannot be approved as the active source")
    source.source_status = payload.decision
    source.currentness_status = payload.currentness_status
    source.reviewer = payload.reviewer.strip()
    source.review_rationale = payload.rationale.strip()
    source.reviewed_at = datetime.now(UTC)
    db.add(source)
    record_audit_event(
        db, event_type="regulatory_source_review", actor=payload.reviewer,
        document_id=source.document_id,
        detail={"source_key": source.source_key, "decision": source.source_status,
                "currentness_status": source.currentness_status,
                "rationale": source.review_rationale},
    )
    db.commit()
    db.refresh(source)
    return source


def create_interpretation(db: Session, payload: InterpretationCreate) -> ApprovedInterpretation:
    source = db.get(RegulatorySource, payload.source_id)
    if source is None:
        raise EvidenceLayerError("Regulatory source not found")
    if source.source_status != "APPROVED":
        raise EvidenceLayerError("Interpretations require an approved regulatory source")
    if payload.obligation_id is not None:
        from app.models.extracted_obligation import ExtractedObligation
        obligation = db.get(ExtractedObligation, payload.obligation_id)
        if obligation is None:
            raise EvidenceLayerError("Extracted obligation not found")
        if obligation.source_document_id != source.document_id or obligation.source_version != source.document_version:
            raise EvidenceLayerError("Obligation must reference the same controlled source document version")
        if obligation.status != "APPROVED":
            raise EvidenceLayerError("Only SME-approved extracted obligations can be linked")
    item = ApprovedInterpretation(
        interpretation_key="INT-" + uuid4().hex[:20].upper(),
        source_id=source.id,
        obligation_id=payload.obligation_id,
        interpretation=payload.interpretation.strip(),
        applicability=payload.applicability,
        rationale=payload.rationale.strip(),
        decision_owner=payload.decision_owner.strip(),
        status="DRAFT",
        created_by=payload.created_by.strip(),
    )
    db.add(item)
    db.flush()
    record_audit_event(
        db, event_type="organisational_interpretation_created", actor=payload.created_by,
        document_id=source.document_id,
        detail={"interpretation_key": item.interpretation_key, "source_key": source.source_key,
                "applicability": item.applicability, "decision_owner": item.decision_owner},
    )
    db.commit()
    db.refresh(item)
    return item


def review_interpretation(
    db: Session, item: ApprovedInterpretation, payload: InterpretationReview
) -> ApprovedInterpretation:
    if item.status != "DRAFT":
        raise EvidenceLayerError("Only draft interpretations can be reviewed; create a new version for changes")
    source = db.get(RegulatorySource, item.source_id)
    if source is None:
        raise EvidenceLayerError("Linked regulatory source not found")
    if payload.decision == "CONFIRMED":
        if source.source_status != "APPROVED":
            raise EvidenceLayerError("Interpretation cannot be confirmed until its source is approved")
        if source.currentness_status != "CURRENT_VERIFIED":
            raise EvidenceLayerError("Interpretation cannot be confirmed until source currentness is verified")
        if item.applicability == "NEEDS_CLARIFICATION":
            raise EvidenceLayerError("Applicability needs clarification before confirmation")
        if payload.reviewer.strip().casefold() == item.decision_owner.strip().casefold():
            raise EvidenceLayerError("Decision owner cannot independently confirm their own interpretation")
    item.status = payload.decision
    item.reviewer = payload.reviewer.strip()
    item.review_rationale = payload.rationale.strip()
    item.reviewed_at = datetime.now(UTC)
    db.add(item)
    record_audit_event(
        db, event_type="organisational_interpretation_review", actor=payload.reviewer,
        document_id=source.document_id,
        detail={"interpretation_key": item.interpretation_key, "decision": item.status,
                "rationale": item.review_rationale, "source_key": source.source_key},
    )
    db.commit()
    db.refresh(item)
    return item


def list_regulatory_sources(db: Session) -> list[RegulatorySource]:
    return list(db.scalars(select(RegulatorySource).order_by(RegulatorySource.id.desc())).all())


def list_interpretations(db: Session, source_id: int | None = None) -> list[ApprovedInterpretation]:
    query = select(ApprovedInterpretation).order_by(ApprovedInterpretation.id.desc())
    if source_id is not None:
        query = query.where(ApprovedInterpretation.source_id == source_id)
    return list(db.scalars(query).all())
