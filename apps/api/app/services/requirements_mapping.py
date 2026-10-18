"""Completeness gates and persistence for draft requirements mappings."""

import json
import re
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.requirements_mapping import RequirementsMapping
from app.schemas.requirements_mapping import (
    RequirementsMappingCreateRequest,
    RequirementsMappingReviewRequest,
)
from app.services.audit import record_audit_event


class RequirementsMappingError(ValueError):
    """A mapping workflow rule was violated."""


def validate_mapping(data: dict[str, Any]) -> list[str]:
    source = data.get("source") or {}
    system = data.get("system") or {}
    clarification = data.get("clarification") or {}
    pbi = data.get("pbi") or {}
    blockers: list[str] = []

    def need(condition: bool, label: str) -> None:
        if not condition:
            blockers.append(label)

    need(
        bool(source.get("sourceId") or source.get("source_id")),
        "Source ID is required",
    )
    need(
        bool(source.get("version") or source.get("sourceVersion")),
        "Source version is required",
    )
    need(bool(source.get("authority")), "Issuing authority is required")
    need(bool(source.get("sourceDocumentId")), "Controlled source document link is required")
    need(bool(source.get("sourceDocumentVersion")), "Captured source document version is required")
    need(bool(source.get("sourceFileHash")), "Captured source file hash is required")
    source_url = str(source.get("url", source.get("sourceUrl", ""))).lower()
    need(source_url.startswith("https://"), "Official HTTPS source URL is required")
    need(
        source.get("approvalStatus") == "APPROVED_FOR_REVIEW",
        "Source review approval is required",
    )
    need(
        bool(source.get("clauseId") or source.get("clause_id")),
        "Stable clause reference is required",
    )
    excerpt = str(source.get("excerpt", source.get("sourceExcerpt", ""))).strip()
    need(len(excerpt) >= 12, "Source excerpt is required")
    need(
        len(str(data.get("obligation", "")).strip()) >= 12,
        "Atomic obligation is required",
    )
    applicability = data.get("applicability")
    need(
        applicability in {"APPLICABLE", "NOT_APPLICABLE"},
        "Applicability must be finalized",
    )
    if applicability == "NOT_APPLICABLE":
        need(
            bool(str(data.get("notApplicableRationale", "")).strip()),
            "Not-applicable rationale is required",
        )

    finding = system.get("finding", system.get("systemFinding", "NOT_ASSESSED"))
    evidence = str(system.get("evidenceRef", system.get("systemEvidence", ""))).strip()
    need(
        finding != "NOT_ASSESSED",
        "System impact must be assessed or explicitly marked unknown",
    )
    need(
        bool(evidence),
        "System evidence reference or explicit unknown reason is required",
    )
    if finding in {"NOT_APPLICABLE", "NOT_APPLICABLE_TO_SYSTEM"}:
        need(
            bool(data.get("systemNotApplicableRationale")),
            "System not-applicable rationale is required",
        )

    need(
        len(str(clarification.get("decision", "")).strip()) >= 12,
        "Interpretation/decision is required",
    )
    need(
        clarification.get("decisionStatus") == "CONFIRMED",
        "Interpretation must be confirmed",
    )
    need(
        bool(clarification.get("owner") or clarification.get("decisionOwner")),
        "Decision owner is required",
    )
    need(
        clarification.get("dependencyStatus", "OPEN") in {"RESOLVED", "NOT_REQUIRED"},
        "Open dependency blocks readiness",
    )
    if clarification.get("question"):
        need(
            bool(clarification.get("questionOwner")),
            "Open clarification must have an owner",
        )

    need(
        len(str(data.get("requirement", "")).strip()) >= 20,
        "Observable business requirement is required",
    )
    need(bool(str(pbi.get("title", "")).strip()), "PBI title is required")
    need(
        len(str(pbi.get("acceptanceCriteria", "")).strip()) >= 20,
        "Testable acceptance criteria are required",
    )
    need(
        len(str(pbi.get("testEvidence", "")).strip()) >= 12,
        "Verification method/evidence is required",
    )
    return blockers


def mapping_to_response(item: RequirementsMapping) -> dict[str, Any]:
    data = json.loads(item.data_json)
    blockers = validate_mapping(data)
    if item.review_status != "APPROVED":
        blockers.append("Independent reviewer approval is required")
    return {
        "id": item.id,
        "mapping_key": item.mapping_key,
        "dossier_id": item.dossier_id,
        "data": data,
        "readiness_status": "READY_FOR_CONTROLLED_REVIEW" if not blockers else "BLOCKED_DRAFT",
        "blockers": blockers,
        "review_status": item.review_status,
        "created_by": item.created_by,
        "reviewer": item.reviewer,
        "reviewer_decision": item.reviewer_decision,
        "reviewer_rationale": item.reviewer_rationale,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "reviewed_at": item.reviewed_at,
    }


def create_mapping(
    db: Session,
    payload: RequirementsMappingCreateRequest,
) -> RequirementsMapping:
    document = db.get(Document, payload.source_document_id)
    if document is None:
        raise RequirementsMappingError("Controlled source document not found")
    data = json.loads(json.dumps(payload.data, ensure_ascii=False))
    source = data["source"]
    excerpt = str(source.get("excerpt", source.get("sourceExcerpt", ""))).strip()
    extracted_text = document.full_extracted_text()
    normalize = lambda value: re.sub(r"\s+", " ", value).strip().casefold()
    if not normalize(excerpt) or normalize(excerpt) not in normalize(extracted_text):
        raise RequirementsMappingError(
            "Source excerpt does not match the selected document's extracted text"
        )
    source["sourceDocumentId"] = document.id
    source["sourceDocumentVersion"] = document.version
    source["sourceFileHash"] = document.file_hash
    item = RequirementsMapping(
        dossier_id=payload.dossier_id,
        data_json=json.dumps(data, ensure_ascii=False),
        readiness_status="BLOCKED_DRAFT",
        review_status="PENDING",
        created_by=payload.created_by,
    )
    db.add(item)
    db.flush()
    record_audit_event(
        db,
        event_type="requirements_mapping_create",
        actor=payload.created_by,
        detail={"mapping_key": item.mapping_key, "dossier_id": item.dossier_id},
    )
    db.commit()
    db.refresh(item)
    return item


def list_mappings(
    db: Session,
    dossier_id: str | None = None,
) -> list[RequirementsMapping]:
    statement = select(RequirementsMapping).order_by(
        RequirementsMapping.created_at.desc(),
        RequirementsMapping.id.desc(),
    )
    if dossier_id:
        statement = statement.where(RequirementsMapping.dossier_id == dossier_id)
    return list(db.scalars(statement).all())


def review_mapping(
    db: Session,
    item: RequirementsMapping,
    payload: RequirementsMappingReviewRequest,
) -> RequirementsMapping:
    blockers = validate_mapping(json.loads(item.data_json))
    if payload.decision == "APPROVED" and blockers:
        raise RequirementsMappingError(
            "Cannot approve mapping with blockers: " + "; ".join(blockers)
        )
    item.reviewer = payload.reviewer
    item.reviewer_decision = payload.decision
    item.reviewer_rationale = payload.rationale
    item.review_status = "APPROVED" if payload.decision == "APPROVED" else payload.decision
    item.readiness_status = (
        "READY_FOR_CONTROLLED_REVIEW"
        if payload.decision == "APPROVED"
        else "BLOCKED_DRAFT"
    )
    item.reviewed_at = datetime.now(UTC)
    db.add(item)
    record_audit_event(
        db,
        event_type="requirements_mapping_review",
        actor=payload.reviewer,
        detail={
            "mapping_key": item.mapping_key,
            "decision": payload.decision,
            "rationale": payload.rationale,
        },
    )
    db.commit()
    db.refresh(item)
    return item
