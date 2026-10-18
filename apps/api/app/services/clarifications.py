"""Clarification queue, decision transitions, and append-only history."""

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.clarification import ClarificationHistory, ClarificationQuestion
from app.models.requirements_mapping import RequirementsMapping
from app.schemas.clarification import ClarificationCreateRequest, ClarificationUpdateRequest
from app.services.audit import record_audit_event


class ClarificationError(ValueError):
    """A clarification workflow transition is invalid."""


def _snapshot(item: ClarificationQuestion) -> dict[str, Any]:
    return {
        "question_key": item.question_key,
        "mapping_id": item.mapping_id,
        "question": item.question,
        "owner": item.owner,
        "status": item.status,
        "answer": item.answer,
        "answered_by": item.answered_by,
        "decision": item.decision,
        "rationale": item.rationale,
        "due_date": item.due_date.isoformat() if item.due_date else None,
        "resolved_by": item.resolved_by,
        "resolved_at": item.resolved_at.isoformat() if item.resolved_at else None,
    }


def _record_history(
    db: Session,
    item: ClarificationQuestion,
    *,
    action: str,
    actor: str,
) -> None:
    db.add(
        ClarificationHistory(
            clarification_id=item.id,
            action=action,
            actor=actor,
            snapshot_json=json.dumps(_snapshot(item), ensure_ascii=False),
        )
    )


def _sync_mapping(db: Session, mapping: RequirementsMapping) -> None:
    data = json.loads(mapping.data_json)
    clarification = data.setdefault("clarification", {})
    questions = list(
        db.scalars(
            select(ClarificationQuestion)
            .where(ClarificationQuestion.mapping_id == mapping.id)
            .order_by(ClarificationQuestion.created_at, ClarificationQuestion.id)
        ).all()
    )
    unresolved = [item for item in questions if item.status != "CONFIRMED"]
    if unresolved:
        clarification["question"] = "\n".join(
            f"{item.question_key}: {item.question}" for item in unresolved
        )
        clarification["questionOwner"] = ", ".join(sorted({item.owner for item in unresolved}))
        clarification["decisionStatus"] = "OPEN"
        clarification["decision"] = "Pending stakeholder decision."
        clarification["dependencyStatus"] = "OPEN"
    else:
        clarification["question"] = "\n".join(
            f"{item.question_key}: {item.question}" for item in questions
        )
        clarification["questionOwner"] = ", ".join(sorted({item.owner for item in questions}))
        clarification["decisionStatus"] = "CONFIRMED"
        clarification["decision"] = "\n".join(
            f"{item.question_key} — Answer: {item.answer or ''}; "
            f"Decision: {item.decision or ''}; Rationale: {item.rationale or ''}"
            for item in questions
        )
        clarification["owner"] = ", ".join(
            sorted({item.resolved_by or item.owner for item in questions})
        )
        clarification["dependencyStatus"] = "RESOLVED"
    mapping.data_json = json.dumps(data, ensure_ascii=False)
    mapping.review_status = "PENDING"
    mapping.readiness_status = "BLOCKED_DRAFT"
    mapping.reviewer = None
    mapping.reviewer_decision = None
    mapping.reviewer_rationale = None
    mapping.reviewed_at = None
    db.add(mapping)


def _response(db: Session, item: ClarificationQuestion) -> dict[str, Any]:
    mapping = db.get(RequirementsMapping, item.mapping_id)
    history = list(
        db.scalars(
            select(ClarificationHistory)
            .where(ClarificationHistory.clarification_id == item.id)
            .order_by(ClarificationHistory.created_at, ClarificationHistory.id)
        ).all()
    )
    return {
        **_snapshot(item),
        "id": item.id,
        "mapping_key": mapping.mapping_key if mapping else "",
        "dossier_id": mapping.dossier_id if mapping else "",
        "created_by": item.created_by,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "history": [
            {
                "id": event.id,
                "action": event.action,
                "actor": event.actor,
                "snapshot": json.loads(event.snapshot_json),
                "created_at": event.created_at,
            }
            for event in history
        ],
    }


def create_question(db: Session, payload: ClarificationCreateRequest) -> dict[str, Any]:
    mapping = db.get(RequirementsMapping, payload.mapping_id)
    if mapping is None:
        raise ClarificationError("Requirements mapping not found")
    item = ClarificationQuestion(
        mapping_id=mapping.id,
        question=payload.question.strip(),
        owner=payload.owner.strip(),
        created_by=payload.created_by.strip(),
        due_date=payload.due_date,
        status="OPEN",
    )
    db.add(item)
    db.flush()
    _record_history(db, item, action="CREATED", actor=payload.created_by)
    _sync_mapping(db, mapping)
    data = json.loads(mapping.data_json)
    source_id = (data.get("source") or {}).get("sourceDocumentId")
    record_audit_event(
        db,
        event_type="clarification_created",
        actor=payload.created_by,
        document_id=source_id if isinstance(source_id, int) else None,
        detail={"question_key": item.question_key, "mapping_key": mapping.mapping_key},
    )
    db.commit()
    db.refresh(item)
    return _response(db, item)


def list_questions(
    db: Session,
    *,
    status: str | None = None,
    mapping_id: int | None = None,
    dossier_id: str | None = None,
) -> list[dict[str, Any]]:
    statement = select(ClarificationQuestion).order_by(
        ClarificationQuestion.created_at.desc(),
        ClarificationQuestion.id.desc(),
    )
    if status:
        statement = statement.where(ClarificationQuestion.status == status)
    if mapping_id:
        statement = statement.where(ClarificationQuestion.mapping_id == mapping_id)
    if dossier_id:
        statement = statement.join(
            RequirementsMapping,
            RequirementsMapping.id == ClarificationQuestion.mapping_id,
        ).where(RequirementsMapping.dossier_id == dossier_id)
    return [_response(db, item) for item in db.scalars(statement).all()]


def get_question(db: Session, question_id: int) -> dict[str, Any] | None:
    item = db.get(ClarificationQuestion, question_id)
    return _response(db, item) if item else None


def update_question(
    db: Session,
    item: ClarificationQuestion,
    payload: ClarificationUpdateRequest,
) -> dict[str, Any]:
    action = payload.action
    if action not in {"ANSWER", "CONFIRM", "REJECT", "REOPEN", "ASSIGN"}:
        raise ClarificationError("Unsupported clarification action")
    actor = payload.actor.strip()
    if action == "ASSIGN":
        if not payload.owner or not payload.owner.strip():
            raise ClarificationError("An owner is required for reassignment")
        item.owner = payload.owner.strip()
    elif action == "ANSWER":
        if item.status not in {"OPEN", "REOPENED"}:
            raise ClarificationError("Only open or reopened questions can be answered")
        if not payload.answer or len(payload.answer.strip()) < 4:
            raise ClarificationError("A substantive answer is required")
        item.answer = payload.answer.strip()
        item.answered_by = actor
        item.decision = None
        item.rationale = None
        item.resolved_by = None
        item.resolved_at = None
        item.status = "ANSWERED"
    elif action == "CONFIRM":
        if item.status != "ANSWERED":
            raise ClarificationError("Answer the question before confirming the decision")
        if not payload.decision or len(payload.decision.strip()) < 4:
            raise ClarificationError("A decision statement is required")
        if not payload.rationale or len(payload.rationale.strip()) < 8:
            raise ClarificationError("A decision rationale is required")
        item.decision = payload.decision.strip()
        item.rationale = payload.rationale.strip()
        item.status = "CONFIRMED"
        item.resolved_by = actor
        item.resolved_at = datetime.now(UTC)
    elif action == "REJECT":
        if item.status != "ANSWERED":
            raise ClarificationError("Answer the question before rejecting its proposed interpretation")
        if not payload.rationale or len(payload.rationale.strip()) < 8:
            raise ClarificationError("A rejection rationale is required")
        item.rationale = payload.rationale.strip()
        item.status = "REJECTED"
        item.resolved_by = actor
        item.resolved_at = datetime.now(UTC)
    elif action == "REOPEN":
        if item.status not in {"CONFIRMED", "REJECTED"}:
            raise ClarificationError("Only a decided question can be reopened")
        if not payload.rationale or len(payload.rationale.strip()) < 8:
            raise ClarificationError("A reason for reopening is required")
        item.decision = None
        item.rationale = payload.rationale.strip()
        item.status = "REOPENED"
        item.resolved_by = None
        item.resolved_at = None
    if payload.due_date is not None:
        item.due_date = payload.due_date
    db.add(item)
    db.flush()
    _record_history(db, item, action=action, actor=actor)
    mapping = db.get(RequirementsMapping, item.mapping_id)
    if mapping is None:
        raise ClarificationError("Requirements mapping not found")
    _sync_mapping(db, mapping)
    data = json.loads(mapping.data_json)
    source_id = (data.get("source") or {}).get("sourceDocumentId")
    record_audit_event(
        db,
        event_type="clarification_" + action.lower(),
        actor=actor,
        document_id=source_id if isinstance(source_id, int) else None,
        detail={"question_key": item.question_key, "mapping_key": mapping.mapping_key},
    )
    db.commit()
    db.refresh(item)
    return _response(db, item)
