import hashlib
import re
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.extracted_obligation import ExtractedObligation
from app.models.requirements_mapping import RequirementsMapping
from app.schemas.extracted_obligation import ObligationExtractionRequest, ObligationReviewRequest
from app.schemas.requirements_mapping import RequirementsMappingCreateRequest
from app.services.audit import record_audit_event
from app.services.requirements_mapping import create_mapping


class ObligationExtractionError(ValueError):
    """Raised when source extraction or review is invalid."""


TERMS = (
    "shall", "must", "must not", "shall not", "is prohibited", "are prohibited",
    "required to", "should", "should not", "may not", "ensure", "maintain",
    "retain", "document", "record", "verify", "validate",
)


def _segments(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+(?=(?:\d+(?:\.\d+)*\s+)?[A-Z0-9(])|\n+", text)
    return [re.sub(r"\s+", " ", part).strip(" \t•-*") for part in parts if len(part.strip()) >= 18]


def _clause_id(text: str, index: int) -> str:
    match = re.match(r"^(\d+(?:\.\d+){0,5}[A-Za-z]?)\s+", text)
    return match.group(1) if match else f"SEG-{index:04d}"


def extract_obligations(
    db: Session,
    document_id: int,
    payload: ObligationExtractionRequest,
) -> list[ExtractedObligation]:
    document = db.get(Document, document_id)
    if document is None:
        raise ObligationExtractionError("Source document not found")
    text = document.full_extracted_text()
    if document.parse_status != "EXTRACTED" or not text.strip():
        raise ObligationExtractionError("Document text extraction must complete first")

    results: list[ExtractedObligation] = []
    for index, excerpt in enumerate(_segments(text), start=1):
        lower = excerpt.casefold()
        matches = [term for term in TERMS if re.search(r"\b" + re.escape(term) + r"\b", lower)]
        if not matches:
            continue
        clause_id = _clause_id(excerpt, index)
        fingerprint = f"{document.file_hash}:{document.version}:{clause_id}:{lower}"
        key = "OBL-" + hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:24].upper()
        existing = db.scalar(
            select(ExtractedObligation).where(
                ExtractedObligation.obligation_key == key
            )
        )
        if existing:
            results.append(existing)
            continue
        strong = any(
            term in matches
            for term in ("shall", "must", "must not", "shall not", "required to")
        )
        item = ExtractedObligation(
            obligation_key=key,
            source_document_id=document.id,
            source_version=document.version,
            source_file_hash=document.file_hash,
            clause_id=clause_id,
            segment_index=index,
            excerpt=excerpt,
            trigger_terms=", ".join(matches),
            extraction_method="RULE_BASED_V1",
            confidence=0.55 if strong else 0.35,
            status="DRAFT",
        )
        db.add(item)
        db.flush()
        results.append(item)

    record_audit_event(
        db,
        event_type="obligation_extraction",
        actor=payload.requested_by,
        document_id=document.id,
        detail={
            "source_version": document.version,
            "source_file_hash": document.file_hash,
            "candidate_count": len(results),
            "method": "RULE_BASED_V1",
        },
    )
    db.commit()
    for item in results:
        db.refresh(item)
    return results


def list_obligations(
    db: Session,
    *,
    document_id: int | None = None,
    status: str | None = None,
) -> list[ExtractedObligation]:
    query = select(ExtractedObligation).order_by(
        ExtractedObligation.source_document_id,
        ExtractedObligation.segment_index,
    )
    if document_id is not None:
        query = query.where(ExtractedObligation.source_document_id == document_id)
    if status:
        query = query.where(ExtractedObligation.status == status)
    return list(db.scalars(query).all())


def review_obligation(
    db: Session,
    item: ExtractedObligation,
    payload: ObligationReviewRequest,
) -> ExtractedObligation:
    if item.status != "DRAFT":
        raise ObligationExtractionError("Only draft candidates can be reviewed")
    item.status = payload.decision
    item.reviewer = payload.reviewer.strip()
    item.review_rationale = payload.rationale.strip()
    item.reviewed_at = datetime.now(UTC)
    db.add(item)
    record_audit_event(
        db,
        event_type="obligation_candidate_review",
        actor=payload.reviewer,
        document_id=item.source_document_id,
        detail={
            "obligation_key": item.obligation_key,
            "decision": item.status,
            "rationale": item.review_rationale,
        },
    )
    db.commit()
    db.refresh(item)
    return item



def create_mapping_from_obligation(
    db: Session,
    item: ExtractedObligation,
    *,
    created_by: str,
) -> RequirementsMapping:
    if item.status != "APPROVED":
        raise ObligationExtractionError("Only approved obligation candidates can seed a mapping")
    if item.mapping_id:
        existing = db.get(RequirementsMapping, item.mapping_id)
        if existing is not None:
            return existing
    document = db.get(Document, item.source_document_id)
    if document is None:
        raise ObligationExtractionError("Source document no longer exists")
    data = {
        "source": {
            "sourceId": f"DOC-{document.id}",
            "title": document.filename,
            "authority": "",
            "version": str(document.version),
            "url": "",
            "approvalStatus": "PENDING_REVIEW",
            "clauseId": item.clause_id,
            "excerpt": item.excerpt,
        },
        "obligation": item.excerpt,
        "applicability": "APPLICABLE",
        "system": {
            "name": "",
            "finding": "UNKNOWN",
            "evidenceRef": "System baseline evidence has not yet been supplied.",
        },
        "clarification": {
            "question": (
                "Which system/process implements this obligation, and what "
                "evidence demonstrates current behaviour?"
            ),
            "questionOwner": "System Owner",
            "decision": "Interpretation pending stakeholder review.",
            "decisionStatus": "OPEN",
            "owner": "Regulatory SME",
            "dependencyStatus": "OPEN",
        },
        "requirement": "",
        "pbi": {"title": "", "acceptanceCriteria": "", "testEvidence": ""},
    }
    mapping = create_mapping(
        db,
        RequirementsMappingCreateRequest(
            dossier_id=f"DOC-{document.id}-V{document.version}",
            created_by=created_by,
            source_document_id=document.id,
            data=data,
        ),
    )
    item.mapping_id = mapping.id
    db.add(item)
    record_audit_event(
        db,
        event_type="obligation_mapping_created",
        actor=created_by,
        document_id=document.id,
        detail={"obligation_key": item.obligation_key, "mapping_key": mapping.mapping_key},
    )
    db.commit()
    db.refresh(item)
    return mapping
