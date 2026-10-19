"""Controlled operations for source verification and interpretation decisions."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.extracted_obligation import ExtractedObligation
from app.models.regulatory_truth import InterpretationDecision, RegulatorySourceRecord
from app.schemas.regulatory_truth import (
    InterpretationCreate,
    InterpretationReview,
    RegulatorySourceCreate,
    RegulatorySourceReview,
)
from app.services.audit import record_audit_event


class RegulatoryTruthError(ValueError):
    """A source or interpretation workflow rule was violated."""


def create_source_record(db: Session, payload: RegulatorySourceCreate) -> RegulatorySourceRecord:
    document = db.get(Document, payload.document_id)
    if document is None:
        raise RegulatoryTruthError("Controlled source document not found")
    existing = db.scalar(
        select(RegulatorySourceRecord).where(
            RegulatorySourceRecord.document_id == payload.document_id
        )
    )
    if existing is not None:
        raise RegulatoryTruthError(
            "A source record already exists for this document; create a new version instead"
        )
    if (
        payload.effective_date
        and payload.publication_date
        and payload.effective_date < payload.publication_date
    ):
        raise RegulatoryTruthError("Effective date cannot precede publication date")
    item = RegulatorySourceRecord(
        document_id=document.id,
        title=payload.title.strip(),
        issuing_authority=payload.issuing_authority.strip(),
        jurisdiction=payload.jurisdiction.strip(),
        document_type=payload.document_type.strip(),
        official_url=payload.official_url.strip(),
        version_label=payload.version_label.strip(),
        publication_date=payload.publication_date,
        effective_date=payload.effective_date,
        applicability_scope=payload.applicability_scope.strip(),
        content_hash=document.file_hash,
        source_status="UNVERIFIED",
        created_by=payload.created_by.strip(),
    )
    db.add(item)
    record_audit_event(
        db, event_type="regulatory_source_record_created", actor=payload.created_by,
        document_id=document.id,
        detail={"source_status": "UNVERIFIED", "content_hash": document.file_hash,
                "authority": payload.issuing_authority, "jurisdiction": payload.jurisdiction},
    )
    db.commit()
    db.refresh(item)
    return item


def review_source_record(
    db: Session, item: RegulatorySourceRecord, payload: RegulatorySourceReview
) -> RegulatorySourceRecord:
    document = db.get(Document, item.document_id)
    if document is None:
        raise RegulatoryTruthError("Controlled source document no longer exists")
    if payload.decision == "VERIFIED":
        if not item.official_url.startswith("https://") or not item.issuing_authority.strip():
            raise RegulatoryTruthError("An HTTPS source URL and issuing authority are required")
        if item.content_hash != document.file_hash:
            raise RegulatoryTruthError(
                "Source hash no longer matches the controlled document; register a new version"
            )
    item.source_status = payload.decision
    item.verified_by = payload.reviewer.strip()
    item.verification_rationale = payload.rationale.strip()
    item.verified_at = datetime.now(UTC)
    db.add(item)
    record_audit_event(
        db, event_type="regulatory_source_record_reviewed", actor=payload.reviewer,
        document_id=document.id,
        detail={"source_record_id": item.id, "decision": payload.decision,
                "rationale": payload.rationale.strip(), "content_hash": item.content_hash},
    )
    db.commit()
    db.refresh(item)
    return item


def create_interpretation(
    db: Session, payload: InterpretationCreate
) -> InterpretationDecision:
    obligation = db.get(ExtractedObligation, payload.obligation_id)
    if obligation is None:
        raise RegulatoryTruthError("Extracted obligation not found")
    if payload.supersedes_id:
        previous = db.get(InterpretationDecision, payload.supersedes_id)
        if previous is None or previous.obligation_id != obligation.id:
            raise RegulatoryTruthError("Superseded decision must belong to the same obligation")
        version = previous.version + 1
    else:
        previous = db.scalar(
            select(InterpretationDecision)
            .where(InterpretationDecision.obligation_id == obligation.id)
            .order_by(InterpretationDecision.version.desc())
        )
        if previous is not None:
            raise RegulatoryTruthError(
                "A prior interpretation exists; specify supersedes_id to create a new version"
            )
        version = 1
    item = InterpretationDecision(
        obligation_id=obligation.id, version=version,
        interpretation=payload.interpretation.strip(), applicability=payload.applicability,
        rationale=payload.rationale.strip(), assumptions=payload.assumptions.strip(),
        unresolved_questions=payload.unresolved_questions.strip(),
        decision_owner=payload.decision_owner.strip(), status="DRAFT",
        submitted_by=payload.submitted_by.strip(), supersedes_id=payload.supersedes_id,
    )
    db.add(item)
    record_audit_event(
        db, event_type="interpretation_decision_created", actor=payload.submitted_by,
        document_id=obligation.source_document_id,
        detail={"obligation_id": obligation.id, "version": version, "status": "DRAFT",
                "applicability": payload.applicability, "supersedes_id": payload.supersedes_id},
    )
    db.commit()
    db.refresh(item)
    return item


def review_interpretation(
    db: Session, item: InterpretationDecision, payload: InterpretationReview
) -> InterpretationDecision:
    if item.status != "DRAFT":
        raise RegulatoryTruthError("Only draft interpretation decisions can be reviewed")
    obligation = db.get(ExtractedObligation, item.obligation_id)
    if obligation is None:
        raise RegulatoryTruthError("Source obligation no longer exists")
    source = db.scalar(
        select(RegulatorySourceRecord).where(
            RegulatorySourceRecord.document_id == obligation.source_document_id
        )
    )
    if payload.decision == "APPROVED":
        if source is None or source.source_status != "VERIFIED":
            raise RegulatoryTruthError(
                "Layer 1 source must be verified before Layer 2 can be approved"
            )
        document = db.get(Document, obligation.source_document_id)
        if document is None or source.content_hash != document.file_hash:
            raise RegulatoryTruthError(
                "Layer 1 source content changed after verification; "
                "re-register and verify the current version"
            )
        if item.applicability == "UNDECIDED":
            raise RegulatoryTruthError("Applicability must be decided before approval")
        if item.unresolved_questions.strip():
            raise RegulatoryTruthError("Resolve or remove unresolved questions before approval")
        if payload.reviewer.strip().casefold() == item.submitted_by.strip().casefold():
            raise RegulatoryTruthError("The submitter cannot approve their own interpretation")
    item.status = payload.decision
    item.reviewed_by = payload.reviewer.strip()
    item.reviewer_role = payload.reviewer_role.strip()
    item.review_rationale = payload.rationale.strip()
    item.approved_at = datetime.now(UTC) if payload.decision == "APPROVED" else None
    db.add(item)
    record_audit_event(
        db, event_type="interpretation_decision_reviewed", actor=payload.reviewer,
        document_id=obligation.source_document_id,
        detail={"interpretation_id": item.id, "obligation_id": item.obligation_id,
                "decision": payload.decision, "reviewer_role": payload.reviewer_role,
                "rationale": payload.rationale.strip()},
    )
    db.commit()
    db.refresh(item)
    return item
