#!/usr/bin/env python3
"""Validate data integrity assessment JSON against docs/schemas/data-integrity-assessment-record.schema.json."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "maras.data-integrity-assessment.v1"
STATUSES = frozenset({"draft", "needs-review", "reviewer-approved", "rejected"})
SUBJECT_KINDS = frozenset({
    "evidence-record", "intake-record", "comparison-record", "ctd-mapping-record",
    "document-review-record", "maras-pbi", "derived-artifact", "controlled-document", "custom",
})
PRINCIPLES = frozenset({
    "attributable", "legible", "contemporaneous", "original", "accurate",
    "complete", "consistent", "enduring", "available",
})
RESULTS = frozenset({"pass", "fail", "needs-review", "na"})
RISKS = frozenset({"low", "medium", "high", "unknown"})
CORE = frozenset({"attributable", "original", "accurate"})
RECORD_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
FORBIDDEN = re.compile(
    r"\b(alcoa[+]?\s+compliant|data\s+integrity\s+compliant|fully\s+compliant|"
    r"certified\s+data\s+integrity)\b",
    re.IGNORECASE,
)


def schema_path() -> Path:
    return Path(__file__).resolve().parents[4] / "docs" / "schemas" / "data-integrity-assessment-record.schema.json"


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
        "schemaVersion", "recordId", "status", "assessmentSubject", "principles",
        "overallRisk", "gaps", "uncertainties", "reviewerActionNeeded", "controls", "assessedAt",
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

    subject = data.get("assessmentSubject")
    if not isinstance(subject, dict):
        errors.append(err(f"{label}.assessmentSubject", "required object"))
    else:
        if subject.get("kind") not in SUBJECT_KINDS:
            errors.append(err(f"{label}.assessmentSubject.kind", f"must be one of {sorted(SUBJECT_KINDS)}"))
        if not str(subject.get("subjectRef") or "").strip():
            errors.append(err(f"{label}.assessmentSubject.subjectRef", "required"))

    principles = data.get("principles")
    seen_p: set[str] = set()
    has_fail_core = False
    has_needs_review = False
    if not isinstance(principles, list) or len(principles) < 5:
        errors.append(err(f"{label}.principles", "must include at least 5 principle results"))
    else:
        for i, pr in enumerate(principles):
            if not isinstance(pr, dict):
                errors.append(err(f"{label}.principles[{i}]", "expected object"))
                continue
            p = pr.get("principle")
            if p not in PRINCIPLES:
                errors.append(err(f"{label}.principles[{i}].principle", f"must be one of {sorted(PRINCIPLES)}"))
            elif p in seen_p:
                errors.append(err(f"{label}.principles[{i}].principle", "duplicate"))
            else:
                seen_p.add(p)
            if pr.get("result") not in RESULTS:
                errors.append(err(f"{label}.principles[{i}].result", f"must be one of {sorted(RESULTS)}"))
            stmt = pr.get("statement")
            if not isinstance(stmt, str) or not stmt.strip():
                errors.append(err(f"{label}.principles[{i}].statement", "required"))
            elif FORBIDDEN.search(stmt):
                errors.append(err(f"{label}.principles[{i}].statement", "forbidden compliance language"))
            if pr.get("result") == "fail" and p in CORE:
                has_fail_core = True
            if pr.get("result") in {"fail", "needs-review"}:
                has_needs_review = True

    risk = data.get("overallRisk")
    if risk not in RISKS:
        errors.append(err(f"{label}.overallRisk", f"must be one of {sorted(RISKS)}"))
    elif has_fail_core and risk not in {"high", "unknown"}:
        errors.append(err(f"{label}.overallRisk", "must be high when core principles fail"))
    elif has_needs_review and risk == "low":
        errors.append(err(f"{label}.overallRisk", "cannot be low when any principle is fail or needs-review"))

    controls = data.get("controls")
    if controls is not None:
        if not isinstance(controls, dict):
            errors.append(err(f"{label}.controls", "expected object"))
        elif controls.get("packageStatus") != "DRAFT_NOT_CONTROLLED":
            errors.append(err(f"{label}.controls.packageStatus", "must be DRAFT_NOT_CONTROLLED"))

    for arr_field in ("gaps", "uncertainties", "reviewerActionNeeded"):
        val = data.get(arr_field)
        if val is None:
            continue
        if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
            errors.append(err(f"{label}.{arr_field}", "must be array of strings"))

    assessed = data.get("assessedAt")
    if not isinstance(assessed, str):
        errors.append(err(f"{label}.assessedAt", "required ISO 8601 string"))
    else:
        try:
            datetime.fromisoformat(assessed.replace("Z", "+00:00"))
        except ValueError:
            errors.append(err(f"{label}.assessedAt", "invalid ISO 8601 datetime"))

    if has_needs_review and status == "draft":
        errors.append(err(f"{label}.status", "must be needs-review when principles need review or fail"))

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
