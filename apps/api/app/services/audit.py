"""Audit event persistence helpers."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent


def record_audit_event(
    db: Session,
    *,
    event_type: str,
    actor: str,
    document_id: int | None = None,
    detail: dict | None = None,
) -> AuditEvent:
    event = AuditEvent(
        event_type=event_type,
        document_id=document_id,
        actor=actor,
        detail=json.dumps(detail or {}, default=str),
    )
    db.add(event)
    return event
