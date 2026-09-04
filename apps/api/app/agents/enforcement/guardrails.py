"""Local Guardrails-shaped schema validation.

Does not call Guardrails AI unless a vendor adapter is configured later.
Rejects forbidden autonomous-approval language and missing required fields.
"""

from __future__ import annotations

import re
from typing import Any

from app.agents.enforcement.exceptions import SchemaGuardrailError
from app.agents.types import AgentTaskRequest, TaskKind

FORBIDDEN_CLAIM = re.compile(
    r"\b(compliant|non[- ]?compliant|inspection[- ]?ready|submission[- ]?ready|"
    r"validated\s+system|part\s*11\s+compliant)\b",
    re.IGNORECASE,
)

REQUIRED_PAYLOAD_KEYS: dict[TaskKind, tuple[str, ...]] = {
    TaskKind.LOOP_ENGINEERING: (),
    TaskKind.ORCHESTRATION_COMPLIANCE: (),
    TaskKind.RAG: (),
    TaskKind.INFRA: (),
    TaskKind.SKILL_ORCHESTRATION: (),
    TaskKind.IDEA_TO_APP: (),
}

OUTPUT_REQUIRED = ("status", "harness_id", "review_disposition")


def _scan_text(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, str):
        if FORBIDDEN_CLAIM.search(value):
            errors.append(
                f"{path}: forbidden autonomous-approval language; "
                "use needs-review language and SME/QA/RA review required"
            )
        return
    if isinstance(value, dict):
        for key, nested in value.items():
            _scan_text(nested, f"{path}.{key}", errors)
        return
    if isinstance(value, list):
        for index, nested in enumerate(value):
            _scan_text(nested, f"{path}[{index}]", errors)


def validate_request_schema(request: AgentTaskRequest, task_kind: TaskKind) -> None:
    errors: list[str] = []
    _scan_text(request.intent, "intent", errors)
    _scan_text(request.payload, "payload", errors)
    for key in REQUIRED_PAYLOAD_KEYS.get(task_kind, ()):
        if key not in request.payload:
            errors.append(f"payload.{key}: required for {task_kind.value}")
    if task_kind is TaskKind.RAG:
        text = request.payload.get("text")
        if text is not None and not isinstance(text, str):
            errors.append("payload.text: must be a string when provided")
        if request.document_id is None and not (isinstance(text, str) and text.strip()):
            errors.append("RAG tasks require payload.text or document_id (derived extract only)")
    if errors:
        raise SchemaGuardrailError("; ".join(errors))


def validate_output_schema(output: dict[str, Any]) -> None:
    errors: list[str] = []
    for key in OUTPUT_REQUIRED:
        if key not in output:
            errors.append(f"output.{key}: required")
    _scan_text(output, "output", errors)
    disposition = str(output.get("review_disposition", ""))
    if disposition not in {"needs-review", "gap-requires-review"}:
        errors.append("output.review_disposition: must be needs-review or gap-requires-review")
    if errors:
        raise SchemaGuardrailError("; ".join(errors))
