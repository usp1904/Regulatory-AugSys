#!/usr/bin/env python3
"""Validate citation and provenance audit JSON against docs/schemas/citation-provenance-audit-record.schema.json."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "maras.citation-provenance-audit.v1"
STATUSES = frozenset({"draft", "needs-review", "reviewer-approved", "rejected"})
SUBJECT_KINDS = frozenset({
    "evidence-record", "intake-record", "comparison-record", "change-impact-record",
    "authoring-record", "document-review-record", "maras-pbi-package", "multi-record-batch", "custom",
})
SCOPE_KINDS = frozenset({
    "evidence-record", "intake-record", "comparison-record", "change-impact-record",
    "authoring-record", "document-review-record", "data-integrity-assessment",
    "ctd-mapping-record", "custom",
})
CATEGORIES = frozenset({
    "missing-excerpt", "missing-citation", "provenance-gap", "metadata-mismatch",
    "unsourced-claim", "stale-source", "non-authoritative-source", "cross-record-conflict",
    "hash-or-locator-gap", "scope-mismatch",
})
SEVERITIES = frozenset({"info", "advisory", "gap", "blocking"})
OVERALL = frozenset({"inconclusive", "minor-gaps", "major-gaps", "needs-review"})
RECORD_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
FINDING_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
FORBIDDEN = re.compile(
    r"\b(citations?\s+(?:verified|certified)|provenance\s+verified|fully\s+traceable|"
    r"audit\s+passed|traceability\s+certified|compliant\s+citations?)\b",
    re.IGNORECASE,
)


def schema_path() -> Path:
    return Path(__file__).resolve().parents[4] / "docs" / "schemas" / "citation-provenance-audit-record.schema.json"


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def err(path: str, message: str) -> str:
    return f"{path}: {message}"


def check_forbidden(text: str, path: str, errors: list[str]) -> None:
    if isinstance(text, str) and FORBIDDEN.search(text):
        errors.append(err(path, "forbidden certification language"))


def validate_record(data: Any, *, label: str = "record") -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return [err(label, "root must be an object")]

    allowed = {
        "schemaVersion", "recordId", "status", "auditSubject", "auditScope",
        "findings", "overallResult", "summary", "gaps", "uncertainties",
        "reviewerActionNeeded", "controls", "auditedAt",
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

    subject = data.get("auditSubject")
    if not isinstance(subject, dict):
        errors.append(err(f"{label}.auditSubject", "required object"))
    else:
        if subject.get("kind") not in SUBJECT_KINDS:
            errors.append(err(f"{label}.auditSubject.kind", f"must be one of {sorted(SUBJECT_KINDS)}"))
        if not str(subject.get("subjectRef") or "").strip():
            errors.append(err(f"{label}.auditSubject.subjectRef", "required"))

    scope = data.get("auditScope")
    if not isinstance(scope, list) or len(scope) < 1:
        errors.append(err(f"{label}.auditScope", "must be non-empty array"))
    else:
        for i, entry in enumerate(scope):
            if not isinstance(entry, dict):
                errors.append(err(f"{label}.auditScope[{i}]", "expected object"))
                continue
            if entry.get("recordKind") not in SCOPE_KINDS:
                errors.append(err(f"{label}.auditScope[{i}].recordKind", f"must be one of {sorted(SCOPE_KINDS)}"))
            if not str(entry.get("recordId") or "").strip():
                errors.append(err(f"{label}.auditScope[{i}].recordId", "required"))

    blocking_count = 0
    gap_count = 0
    findings = data.get("findings")
    if not isinstance(findings, list):
        errors.append(err(f"{label}.findings", "must be array"))
        findings = []
    else:
        seen_f: set[str] = set()
        for i, finding in enumerate(findings):
            if not isinstance(finding, dict):
                errors.append(err(f"{label}.findings[{i}]", "expected object"))
                continue
            fid = finding.get("findingId")
            if not isinstance(fid, str) or not FINDING_ID.match(fid):
                errors.append(err(f"{label}.findings[{i}].findingId", "missing or invalid"))
            elif fid in seen_f:
                errors.append(err(f"{label}.findings[{i}].findingId", "duplicate"))
            else:
                seen_f.add(fid)
            if finding.get("category") not in CATEGORIES:
                errors.append(err(f"{label}.findings[{i}].category", f"must be one of {sorted(CATEGORIES)}"))
            sev = finding.get("severity")
            if sev not in SEVERITIES:
                errors.append(err(f"{label}.findings[{i}].severity", f"must be one of {sorted(SEVERITIES)}"))
            elif sev == "blocking":
                blocking_count += 1
            elif sev == "gap":
                gap_count += 1
            stmt = finding.get("statement")
            if not isinstance(stmt, str) or not stmt.strip():
                errors.append(err(f"{label}.findings[{i}].statement", "required"))
            else:
                check_forbidden(stmt, f"{label}.findings[{i}].statement", errors)
            rec = finding.get("recommendation")
            if rec is not None:
                check_forbidden(str(rec), f"{label}.findings[{i}].recommendation", errors)

    overall = data.get("overallResult")
    if overall not in OVERALL:
        errors.append(err(f"{label}.overallResult", f"must be one of {sorted(OVERALL)}"))
    elif blocking_count > 0 and overall not in {"major-gaps", "needs-review"}:
        errors.append(err(f"{label}.overallResult", "must be major-gaps or needs-review when blocking findings exist"))
    elif blocking_count == 0 and gap_count > 0 and overall == "inconclusive":
        errors.append(err(f"{label}.overallResult", "cannot be inconclusive when gap findings exist"))

    controls = data.get("controls")
    if controls is not None:
        if not isinstance(controls, dict):
            errors.append(err(f"{label}.controls", "expected object"))
        else:
            if controls.get("packageStatus") != "DRAFT_NOT_CONTROLLED":
                errors.append(err(f"{label}.controls.packageStatus", "must be DRAFT_NOT_CONTROLLED"))
            if controls.get("auditSignedOff") is True:
                errors.append(err(f"{label}.controls.auditSignedOff", "must be false"))

    for arr_field in ("gaps", "uncertainties", "reviewerActionNeeded"):
        val = data.get(arr_field)
        if val is None:
            continue
        if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
            errors.append(err(f"{label}.{arr_field}", "must be array of strings"))

    audited = data.get("auditedAt")
    if not isinstance(audited, str):
        errors.append(err(f"{label}.auditedAt", "required ISO 8601 string"))
    else:
        try:
            datetime.fromisoformat(audited.replace("Z", "+00:00"))
        except ValueError:
            errors.append(err(f"{label}.auditedAt", "invalid ISO 8601 datetime"))

    if blocking_count > 0 and status == "draft":
        errors.append(err(f"{label}.status", "must be needs-review when blocking findings exist"))

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
