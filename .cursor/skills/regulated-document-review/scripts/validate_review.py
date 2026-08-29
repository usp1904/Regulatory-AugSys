#!/usr/bin/env python3
"""Validate regulated document review JSON against docs/schemas/document-review-record.schema.json."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "maras.document-review.v1"
STATUSES = frozenset({"draft", "needs-review", "reviewer-approved", "rejected"})
SUBJECT_KINDS = frozenset({
    "evidence-record", "intake-record", "comparison-record", "ctd-mapping-record",
    "maras-pbi-package", "controlled-document", "inspection-pack", "custom",
})
DECISIONS = frozenset({
    "NOT_REVIEWED", "NEEDS_SECOND_REVIEW", "CLARIFICATION_REQUIRED",
    "SME_REVIEW_ATTESTED_DRAFT", "REJECTED",
})
CHECK_RESULTS = frozenset({"pass", "fail", "na", "needs-review"})
SEVERITIES = frozenset({"info", "advisory", "gap", "blocking"})
READINESS = frozenset({"NOT_READY", "CONDITIONALLY_READY", "READY"})
RECORD_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
FINDING_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
FORBIDDEN = re.compile(
    r"\b(compliant|approved\s+for\s+use|inspection[- ]?ready|submission[- ]?ready|"
    r"electronically\s+signed|regulatory\s+approval)\b",
    re.IGNORECASE,
)


def schema_path() -> Path:
    return Path(__file__).resolve().parents[4] / "docs" / "schemas" / "document-review-record.schema.json"


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def err(path: str, message: str) -> str:
    return f"{path}: {message}"


def validate_record(data: Any, *, label: str = "record") -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return [err(label, "root must be an object")]

    allowed = {
        "schemaVersion", "recordId", "status", "reviewSubject", "reviewer",
        "reviewDecision", "checklist", "findings", "gaps", "uncertainties",
        "reviewerActionNeeded", "evidenceReadiness", "controls", "preparedAt",
    }
    extra = set(data) - allowed
    if extra:
        errors.append(err(label, f"unexpected root fields: {sorted(extra)}"))

    if data.get("schemaVersion") != SCHEMA_VERSION:
        errors.append(err(f"{label}.schemaVersion", f"must be {SCHEMA_VERSION!r}"))

    rid = data.get("recordId")
    if not isinstance(rid, str) or not RECORD_ID.match(rid):
        errors.append(err(f"{label}.recordId", "missing or invalid"))

    status = data.get("status")
    if status not in STATUSES:
        errors.append(err(f"{label}.status", f"must be one of {sorted(STATUSES)}"))

    subject = data.get("reviewSubject")
    if not isinstance(subject, dict):
        errors.append(err(f"{label}.reviewSubject", "required object"))
    else:
        if subject.get("kind") not in SUBJECT_KINDS:
            errors.append(err(f"{label}.reviewSubject.kind", f"must be one of {sorted(SUBJECT_KINDS)}"))
        if not str(subject.get("subjectRef") or "").strip():
            errors.append(err(f"{label}.reviewSubject.subjectRef", "required"))

    decision = data.get("reviewDecision")
    if decision not in DECISIONS:
        errors.append(err(f"{label}.reviewDecision", f"must be one of {sorted(DECISIONS)}"))

    reviewer = data.get("reviewer")
    if reviewer is not None:
        if not isinstance(reviewer, dict):
            errors.append(err(f"{label}.reviewer", "expected object"))
        else:
            for f in ("name", "role"):
                if not str(reviewer.get(f) or "").strip():
                    errors.append(err(f"{label}.reviewer.{f}", "required when reviewer present"))
            if decision == "SME_REVIEW_ATTESTED_DRAFT" and not str(reviewer.get("comment") or "").strip():
                errors.append(err(f"{label}.reviewer.comment", "required for SME_REVIEW_ATTESTED_DRAFT"))

    if decision == "SME_REVIEW_ATTESTED_DRAFT":
        if not reviewer:
            errors.append(err(f"{label}.reviewer", "required for SME_REVIEW_ATTESTED_DRAFT"))
        if status not in {"needs-review", "reviewer-approved"}:
            errors.append(err(f"{label}.status", "invalid for attested draft"))

    if decision == "NOT_REVIEWED" and status == "reviewer-approved":
        errors.append(err(f"{label}.status", "cannot be reviewer-approved when NOT_REVIEWED"))

    checklist = data.get("checklist")
    if not isinstance(checklist, list) or len(checklist) < 1:
        errors.append(err(f"{label}.checklist", "must be non-empty array"))
    else:
        for i, item in enumerate(checklist):
            if not isinstance(item, dict):
                errors.append(err(f"{label}.checklist[{i}]", "expected object"))
                continue
            for req in ("id", "label", "result"):
                if req not in item:
                    errors.append(err(f"{label}.checklist[{i}].{req}", "required"))
            if item.get("result") not in CHECK_RESULTS:
                errors.append(err(f"{label}.checklist[{i}].result", f"must be one of {sorted(CHECK_RESULTS)}"))

    findings = data.get("findings") or []
    if not isinstance(findings, list):
        errors.append(err(f"{label}.findings", "expected array"))
    else:
        for i, finding in enumerate(findings):
            if not isinstance(finding, dict):
                errors.append(err(f"{label}.findings[{i}]", "expected object"))
                continue
            fid = finding.get("findingId")
            if not isinstance(fid, str) or not FINDING_ID.match(fid):
                errors.append(err(f"{label}.findings[{i}].findingId", "invalid"))
            if finding.get("severity") not in SEVERITIES:
                errors.append(err(f"{label}.findings[{i}].severity", f"must be one of {sorted(SEVERITIES)}"))
            stmt = finding.get("statement")
            if isinstance(stmt, str) and FORBIDDEN.search(stmt):
                errors.append(err(f"{label}.findings[{i}].statement", "forbidden approval language"))

    for arr_field in ("gaps", "uncertainties", "reviewerActionNeeded"):
        val = data.get(arr_field)
        if val is None:
            continue
        if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
            errors.append(err(f"{label}.{arr_field}", "must be array of strings"))

    readiness = data.get("evidenceReadiness")
    if readiness is not None:
        if not isinstance(readiness, dict):
            errors.append(err(f"{label}.evidenceReadiness", "expected object"))
        else:
            if readiness.get("decision") not in READINESS:
                errors.append(err(f"{label}.evidenceReadiness.decision", f"must be one of {sorted(READINESS)}"))
            if readiness.get("submissionReady") is not False:
                errors.append(err(f"{label}.evidenceReadiness.submissionReady", "must be false"))

    controls = data.get("controls")
    if controls is not None:
        if not isinstance(controls, dict):
            errors.append(err(f"{label}.controls", "expected object"))
        else:
            if controls.get("electronicSignature") is not False:
                errors.append(err(f"{label}.controls.electronicSignature", "must be false"))
            if controls.get("packageStatus") != "DRAFT_NOT_CONTROLLED":
                errors.append(err(f"{label}.controls.packageStatus", "must be DRAFT_NOT_CONTROLLED"))

    prepared = data.get("preparedAt")
    if not isinstance(prepared, str):
        errors.append(err(f"{label}.preparedAt", "required ISO 8601 string"))
    else:
        try:
            datetime.fromisoformat(prepared.replace("Z", "+00:00"))
        except ValueError:
            errors.append(err(f"{label}.preparedAt", "invalid ISO 8601 datetime"))

    has_fail = isinstance(checklist, list) and any(
        isinstance(c, dict) and c.get("result") in {"fail", "needs-review"} for c in checklist
    )
    has_blocking = isinstance(findings, list) and any(
        isinstance(f, dict) and f.get("severity") == "blocking" for f in findings
    )
    if (has_fail or has_blocking) and readiness and readiness.get("decision") == "READY":
        errors.append(err(f"{label}.evidenceReadiness.decision", "cannot be READY with failing checklist or blocking findings"))
    if (has_fail or has_blocking) and decision == "SME_REVIEW_ATTESTED_DRAFT":
        errors.append(err(f"{label}.reviewDecision", "cannot attest draft with failing checklist or blocking findings"))

    return errors


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if not schema_path().is_file():
        print(f"Schema not found: {schema_path()}", file=sys.stderr)
        return 2

    failed = False
    for arg in argv[1:]:
        path = Path(arg)
        try:
            data = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"{path}: {exc}", file=sys.stderr)
            failed = True
            continue
        errors = validate_record(data, label=str(path))
        if errors:
            failed = True
            for line in errors:
                print(line, file=sys.stderr)
        else:
            print(f"OK: {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
