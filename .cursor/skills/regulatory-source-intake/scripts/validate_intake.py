#!/usr/bin/env python3
"""Validate regulatory source intake JSON against docs/schemas/source-intake-record.schema.json."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "maras.source-intake.v1"
STATUSES = frozenset({"draft", "needs-review", "reviewer-approved", "rejected"})
INTAKE_KINDS = frozenset({"regulatory-source", "requirement-text"})
SOURCE_CATEGORIES = frozenset({
    "official-authority", "official-translation", "approved-internal-controlled",
    "internal-draft", "industry-commentary", "machine-summary",
})
DOC_CLASSES = frozenset({
    "Regulation", "Guidance", "Guideline", "Licensed standard", "SOP", "Policy",
    "Work instruction", "Validation package", "Requirement", "Unknown",
})
APPROVAL_STATUSES = frozenset({"SME_PENDING", "SME_APPROVED", "BLOCKED_LICENSE", "REJECTED"})
DOC_STATUSES = frozenset({"current", "superseded", "draft", "unknown"})
PARSE_STATUSES = frozenset({
    "PARSED", "EMPTY", "INVALID_JSON", "UNSUPPORTED_BINARY", "TOO_LARGE", "OCR_PENDING",
})
REVIEW_FLAGS = frozenset({
    "unclear", "conflicting", "translated", "superseded",
    "ocr-derived", "non-authoritative", "stale-document",
})
SHA256 = re.compile(r"^[a-f0-9]{64}$")
RECORD_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FORBIDDEN = re.compile(
    r"\b(compliant|non[- ]?compliant|inspection[- ]?ready|submission[- ]?ready)\b",
    re.IGNORECASE,
)


def schema_path() -> Path:
    return Path(__file__).resolve().parents[4] / "docs" / "schemas" / "source-intake-record.schema.json"


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def err(path: str, message: str) -> str:
    return f"{path}: {message}"


def validate_iso_datetime(value: str, path: str, errors: list[str]) -> None:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(err(path, f"invalid ISO 8601 datetime: {value!r}"))


def maras_drive_eligible(data: dict) -> tuple[bool, list[str]]:
    """Mirror evaluateSourceProductionGate required fields for regulatory-source."""
    missing: list[str] = []
    meta = data.get("metadata") or {}
    parse = data.get("parse") or {}
    original = data.get("original") or {}
    url = meta.get("officialUrl") or ""
    if not (isinstance(url, str) and url.startswith(("http://", "https://"))):
        missing.append("officialUrl")
    if not str(meta.get("issuingAuthority") or "").strip():
        missing.append("authority")
    if not str(meta.get("documentClass") or "").strip():
        missing.append("documentClass")
    if not str(meta.get("effectiveDate") or "").strip():
        missing.append("effectiveDate")
    if not str(parse.get("capturedAt") or "").strip():
        missing.append("capturedAt")
    if not SHA256.match(str(original.get("fileHash") or "")):
        missing.append("fileHash")
    if not str(meta.get("licenseTag") or "").strip():
        missing.append("licenseTag")
    if meta.get("sourceApprovalStatus") != "SME_APPROVED":
        missing.append("sourceApprovalStatus")
    license_blocked = meta.get("licenseTag") == "LICENSE_REQUIRED"
    parse_ok = parse.get("parseStatus") == "PARSED"
    excerpt_ok = bool(str(parse.get("derivedArtifactRef") or "").strip())
    passed = not missing and not license_blocked and parse_ok and excerpt_ok
    return passed, missing


def validate_record(data: Any, *, label: str = "record") -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return [err(label, "root must be an object")]

    allowed = {
        "schemaVersion", "recordId", "status", "intakeKind", "sourceCategory",
        "original", "metadata", "parse", "gate", "reviewFlags",
        "uncertainties", "reviewerActionNeeded", "intakeAt",
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

    intake_kind = data.get("intakeKind")
    if intake_kind not in INTAKE_KINDS:
        errors.append(err(f"{label}.intakeKind", f"must be one of {sorted(INTAKE_KINDS)}"))

    category = data.get("sourceCategory")
    if category not in SOURCE_CATEGORIES:
        errors.append(err(f"{label}.sourceCategory", f"must be one of {sorted(SOURCE_CATEGORIES)}"))

    original = data.get("original")
    if not isinstance(original, dict):
        errors.append(err(f"{label}.original", "required object"))
    else:
        if original.get("immutable") is not True:
            errors.append(err(f"{label}.original.immutable", "must be true"))
        if not SHA256.match(str(original.get("fileHash") or "")):
            errors.append(err(f"{label}.original.fileHash", "must be SHA-256 hex (64 chars)"))
        if not isinstance(original.get("byteSize"), int) or original["byteSize"] < 0:
            errors.append(err(f"{label}.original.byteSize", "must be non-negative integer"))

    meta = data.get("metadata")
    if not isinstance(meta, dict):
        errors.append(err(f"{label}.metadata", "required object"))
    else:
        for req in ("jurisdiction", "issuingAuthority", "documentClass", "documentVersion", "language", "documentStatus"):
            if not str(meta.get(req) or "").strip():
                errors.append(err(f"{label}.metadata.{req}", "required"))
        if meta.get("documentClass") not in DOC_CLASSES:
            errors.append(err(f"{label}.metadata.documentClass", f"must be one of {sorted(DOC_CLASSES)}"))
        if meta.get("documentStatus") not in DOC_STATUSES:
            errors.append(err(f"{label}.metadata.documentStatus", f"must be one of {sorted(DOC_STATUSES)}"))
        sas = meta.get("sourceApprovalStatus")
        if sas is not None and sas not in APPROVAL_STATUSES:
            errors.append(err(f"{label}.metadata.sourceApprovalStatus", f"must be one of {sorted(APPROVAL_STATUSES)}"))
        ed = meta.get("effectiveDate")
        if ed is not None and ed != "" and (not isinstance(ed, str) or not ISO_DATE.match(ed)):
            errors.append(err(f"{label}.metadata.effectiveDate", "must be YYYY-MM-DD or null"))

    parse = data.get("parse")
    if parse is not None:
        if not isinstance(parse, dict):
            errors.append(err(f"{label}.parse", "expected object"))
        elif parse.get("parseStatus") not in PARSE_STATUSES:
            errors.append(err(f"{label}.parse.parseStatus", f"must be one of {sorted(PARSE_STATUSES)}"))

    gate = data.get("gate")
    if not isinstance(gate, dict):
        errors.append(err(f"{label}.gate", "required object"))
    else:
        if gate.get("decision") not in {"DRIVE", "HOLD"}:
            errors.append(err(f"{label}.gate.decision", "must be DRIVE or HOLD"))
        if not isinstance(gate.get("passed"), bool):
            errors.append(err(f"{label}.gate.passed", "must be boolean"))
        if not str(gate.get("reason") or "").strip():
            errors.append(err(f"{label}.gate.reason", "required"))

    flags = data.get("reviewFlags") or []
    if not isinstance(flags, list):
        errors.append(err(f"{label}.reviewFlags", "expected array"))
    else:
        for i, flag in enumerate(flags):
            if flag not in REVIEW_FLAGS:
                errors.append(err(f"{label}.reviewFlags[{i}]", f"unknown flag {flag!r}"))

    for arr_field in ("uncertainties", "reviewerActionNeeded"):
        val = data.get(arr_field)
        if val is None:
            continue
        if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
            errors.append(err(f"{label}.{arr_field}", "must be array of strings"))
        else:
            for i, text in enumerate(val):
                if FORBIDDEN.search(text):
                    errors.append(err(f"{label}.{arr_field}[{i}]", "forbidden compliance language"))

    intake_at = data.get("intakeAt")
    if not isinstance(intake_at, str):
        errors.append(err(f"{label}.intakeAt", "required ISO 8601 string"))
    else:
        validate_iso_datetime(intake_at, f"{label}.intakeAt", errors)

    # Consistency rules
    if flags and status == "draft":
        errors.append(err(f"{label}.status", "must be needs-review when reviewFlags present"))
    if category in {"machine-summary", "industry-commentary"} and status == "draft":
        errors.append(err(f"{label}.status", "must be needs-review for non-authoritative categories"))
    if category == "internal-draft" and gate.get("decision") == "DRIVE":
        errors.append(err(f"{label}.gate.decision", "internal-draft must not DRIVE without reviewer-approved"))
    if status != "reviewer-approved" and gate.get("decision") == "DRIVE" and meta.get("sourceApprovalStatus") != "SME_APPROVED":
        errors.append(err(f"{label}.gate", "DRIVE requires SME_APPROVED and reviewer-approved record status"))

    if intake_kind == "regulatory-source" and isinstance(gate, dict) and gate.get("decision") == "DRIVE":
        eligible, missing = maras_drive_eligible(data)
        if not eligible:
            errors.append(err(f"{label}.gate", f"DRIVE claimed but gate checks fail; missing: {missing}"))

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
