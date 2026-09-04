"""Select harness, enforce gates, execute local adapter, audit the run."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.agents.adapters import ADAPTERS
from app.agents.enforcement.authz import authorize_agent_request
from app.agents.enforcement.guardrails import validate_output_schema, validate_request_schema
from app.agents.enforcement.tokens import optimize_tokens
from app.agents.selector import select_harness
from app.agents.types import (
    AgentRunResult,
    AgentTaskRequest,
    EnforcementReport,
    ReviewDisposition,
    SelectionResult,
)
from app.models.document import Document
from app.services.audit import record_audit_event


def _derived_text(db: Session, request: AgentTaskRequest) -> str:
    parts = [request.intent]
    payload_text = request.payload.get("text")
    if isinstance(payload_text, str) and payload_text.strip():
        parts.append(payload_text.strip())
    if request.document_id is not None:
        document = db.get(Document, request.document_id)
        if document is not None:
            # Derived extract only — never open storage_path original bytes.
            extracted = document.full_extracted_text()
            if extracted:
                parts.append(extracted)
    return "\n\n".join(parts)


def run_agent_task(db: Session, request: AgentTaskRequest) -> AgentRunResult:
    authorize_agent_request(request)
    selection: SelectionResult = select_harness(request.intent, request.task_kind)
    validate_request_schema(request, selection.task_kind)
    derived = _derived_text(db, request)
    optimized_text, chunks, token_report = optimize_tokens(derived)
    adapter = ADAPTERS[selection.harness_id]
    output: dict[str, Any] = adapter.execute(
        request=request,
        selection=selection,
        optimized_text=optimized_text,
        chunks=chunks,
    )
    validate_output_schema(output)
    event = record_audit_event(
        db,
        event_type="agent_run",
        actor=request.actor,
        document_id=request.document_id,
        detail={
            "task_kind": selection.task_kind.value,
            "harness_id": selection.harness_id.value,
            "inferred_kind": selection.inferred_kind.value,
            "explicit_kind": selection.explicit_kind.value if selection.explicit_kind else None,
            "matched_signals": selection.matched_signals,
            "token_optimization": token_report.model_dump(),
            "send_external": request.send_external,
            "review_disposition": output.get("review_disposition"),
        },
    )
    db.commit()
    db.refresh(event)
    notes = list(output.get("notes") or [])
    notes.append("Audit event recorded for traceability. Not a regulatory approval.")
    return AgentRunResult(
        status=str(output.get("status") or "completed-local"),
        selection=selection,
        enforcement=EnforcementReport(
            schema_valid=True,
            authorized=True,
            audit_event_id=event.id,
            token_optimization=token_report,
            data_governance="local-derived-only",
        ),
        output=output,
        review_disposition=ReviewDisposition(output["review_disposition"]),
        notes=notes,
    )
