#!/usr/bin/env python3
"""Validate regulatory evidence JSON against docs/schemas/evidence-record.schema.json.

Usage:
  python3 validate_evidence.py <record.json> [<record2.json> ...]

Exit 0 when all records pass. Exit 1 on validation failure.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "maras.evidence-record.v1"
RECORD_STATUSES = frozenset({"draft", "needs-review", "reviewer-approved", "rejected"})
SOURCE_CLASSES = frozenset({"official-authority", "approved-internal-controlled"})
DOC_STATUSES = frozenset({"current", "superseded", "draft", "unknown"})
LOCATOR_KINDS = frozenset({"url", "file"})
CLAIM_TYPES = frozenset({
    "requirement", "definition", "obligation", "prohibition", "permission",
    "scope", "procedure", "coverage", "gap", "uncertainty",
})
REVIEW_FLAGS = frozenset({
    "unclear", "conflicting", "translated", "superseded",
    "ocr-derived", "non-authoritative",
})
FORBIDDEN_PHRASES = re.compile(
    r"\b("
    r"compliant|non[- ]?compliant|in compliance|"
    r"submission[- ]?ready|inspection[- ]?ready|"
    r"(?:is|are|was|were)\s+(?:approved|cleared|certified|validated)\b|"
    r"regulatory approval"
    r")\b",
    re.IGNORECASE,
)
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RECORD_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
CLAIM_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def schema_path() -> Path:
    return Path(__file__).resolve().parents[4] / "docs" / "schemas" / "evidence-record.schema.json"


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def err(path: str, message: str) -> str:
    return f"{path}: {message}"


def check_type(value: Any, expected: str, path: str, errors: list[str]) -> None:
    if expected == "string" and not isinstance(value, str):
        errors.append(err(path, "expected string"))
    elif expected == "array" and not isinstance(value, list):
        errors.append(err(path, "expected array"))
    elif expected == "object" and not isinstance(value, dict):
        errors.append(err(path, "expected object"))


def validate_iso_datetime(value: str, path: str, errors: list[str]) -> None:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(err(path, f"invalid ISO 8601 datetime: {value!r}"))


def validate_locator(locator: Any, path: str, errors: list[str], *, require_kind: bool = True) -> None:
    if not isinstance(locator, dict):
        errors.append(err(path, "expected object"))
        return
    extra = set(locator) - {"kind", "url", "fileIdentifier", "page", "section", "chunkIdentifier"}
    if extra:
        errors.append(err(path, f"unexpected fields: {sorted(extra)}"))
    if require_kind:
        kind = locator.get("kind")
        if kind not in LOCATOR_KINDS:
            errors.append(err(f"{path}.kind", f"must be one of {sorted(LOCATOR_KINDS)}"))
        elif kind == "url" and not locator.get("url"):
            errors.append(err(f"{path}.url", "required when kind=url"))
        elif kind == "file" and not locator.get("fileIdentifier"):
            errors.append(err(f"{path}.fileIdentifier", "required when kind=file"))


def validate_claim(claim: Any, path: str, errors: list[str]) -> list[str]:
    flags: list[str] = []
    if not isinstance(claim, dict):
        errors.append(err(path, "expected object"))
        return flags
    allowed = {
        "claimId", "claimType", "statement", "verbatimExcerpt",
        "excerptLocator", "reviewFlags", "reviewerActionNeeded",
    }
    extra = set(claim) - allowed
    if extra:
        errors.append(err(path, f"unexpected fields: {sorted(extra)}"))
    for field in ("claimId", "claimType", "statement", "verbatimExcerpt", "excerptLocator"):
        if field not in claim:
            errors.append(err(f"{path}.{field}", "required"))
    cid = claim.get("claimId")
    if isinstance(cid, str) and not CLAIM_ID.match(cid):
        errors.append(err(f"{path}.claimId", "invalid pattern"))
    ctype = claim.get("claimType")
    if ctype not in CLAIM_TYPES:
        errors.append(err(f"{path}.claimType", f"must be one of {sorted(CLAIM_TYPES)}"))
    for text_field in ("statement", "verbatimExcerpt"):
        val = claim.get(text_field)
        if isinstance(val, str):
            if not val.strip():
                errors.append(err(f"{path}.{text_field}", "must not be empty"))
            if FORBIDDEN_PHRASES.search(val):
                errors.append(err(f"{path}.{text_field}", "contains forbidden compliance language"))
    locator = claim.get("excerptLocator")
    if locator is not None:
        if not isinstance(locator, dict):
            errors.append(err(f"{path}.excerptLocator", "expected object"))
        else:
            bad = set(locator) - {"page", "section", "chunkIdentifier"}
            if bad:
                errors.append(err(f"{path}.excerptLocator", f"unexpected fields: {sorted(bad)}"))
    rf = claim.get("reviewFlags", [])
    if rf is None:
        rf = []
    if not isinstance(rf, list):
        errors.append(err(f"{path}.reviewFlags", "expected array"))
    else:
        for i, flag in enumerate(rf):
            if flag not in REVIEW_FLAGS:
                errors.append(err(f"{path}.reviewFlags[{i}]", f"unknown flag {flag!r}"))
            else:
                flags.append(flag)
        if len(rf) != len(set(rf)):
            errors.append(err(f"{path}.reviewFlags", "duplicate flags"))
    return flags


def validate_record(data: Any, *, label: str = "record") -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return [err(label, "root must be an object")]

    allowed_root = {
        "schemaVersion", "recordId", "status", "sourceClass", "provenance",
        "claims", "coverageNotes", "gaps", "uncertainties",
        "reviewerActionNeeded", "reviewerNotes", "extractedAt",
    }
    extra = set(data) - allowed_root
    if extra:
        errors.append(err(label, f"unexpected root fields: {sorted(extra)}"))

    if data.get("schemaVersion") != SCHEMA_VERSION:
        errors.append(err(f"{label}.schemaVersion", f"must be {SCHEMA_VERSION!r}"))

    rid = data.get("recordId")
    if not isinstance(rid, str) or not RECORD_ID.match(rid):
        errors.append(err(f"{label}.recordId", "missing or invalid"))

    status = data.get("status")
    if status not in RECORD_STATUSES:
        errors.append(err(f"{label}.status", f"must be one of {sorted(RECORD_STATUSES)}"))

    source_class = data.get("sourceClass")
    if source_class not in SOURCE_CLASSES:
        errors.append(err(f"{label}.sourceClass", f"must be one of {sorted(SOURCE_CLASSES)}"))

    prov = data.get("provenance")
    claim_flags: list[str] = []
    if not isinstance(prov, dict):
        errors.append(err(f"{label}.provenance", "required object"))
    else:
        prov_allowed = {
            "jurisdiction", "issuingAuthority", "documentVersion", "effectiveDate",
            "language", "documentStatus", "sourceLocator",
        }
        prov_extra = set(prov) - prov_allowed
        if prov_extra:
            errors.append(err(f"{label}.provenance", f"unexpected fields: {sorted(prov_extra)}"))
        for req in ("jurisdiction", "issuingAuthority", "documentVersion", "language", "documentStatus", "sourceLocator"):
            if req not in prov:
                errors.append(err(f"{label}.provenance.{req}", "required"))
        ed = prov.get("effectiveDate")
        if ed is not None and ed != "":
            if not isinstance(ed, str) or not ISO_DATE.match(ed):
                errors.append(err(f"{label}.provenance.effectiveDate", "must be YYYY-MM-DD or null"))
        ds = prov.get("documentStatus")
        if ds not in DOC_STATUSES:
            errors.append(err(f"{label}.provenance.documentStatus", f"must be one of {sorted(DOC_STATUSES)}"))
        validate_locator(prov.get("sourceLocator"), f"{label}.provenance.sourceLocator", errors)
        sl = prov.get("sourceLocator") or {}
        if source_class == "official-authority" and sl.get("kind") != "url":
            errors.append(err(f"{label}.provenance.sourceLocator", "official-authority requires kind=url"))
        if source_class == "approved-internal-controlled" and sl.get("kind") != "file":
            errors.append(err(f"{label}.provenance.sourceLocator", "approved-internal-controlled requires kind=file"))

    claims = data.get("claims")
    if not isinstance(claims, list) or len(claims) < 1:
        errors.append(err(f"{label}.claims", "must be a non-empty array"))
    else:
        seen_ids: set[str] = set()
        for i, claim in enumerate(claims):
            flags = validate_claim(claim, f"{label}.claims[{i}]", errors)
            claim_flags.extend(flags)
            cid = claim.get("claimId") if isinstance(claim, dict) else None
            if isinstance(cid, str):
                if cid in seen_ids:
                    errors.append(err(f"{label}.claims[{i}].claimId", "duplicate claimId"))
                seen_ids.add(cid)

    for arr_field in ("coverageNotes", "gaps", "uncertainties", "reviewerActionNeeded"):
        val = data.get(arr_field)
        if val is None:
            continue
        if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
            errors.append(err(f"{label}.{arr_field}", "must be an array of strings"))
        else:
            for i, text in enumerate(val):
                if FORBIDDEN_PHRASES.search(text):
                    errors.append(err(f"{label}.{arr_field}[{i}]", "forbidden compliance language"))

    notes = data.get("reviewerNotes")
    if notes is not None and isinstance(notes, str) and FORBIDDEN_PHRASES.search(notes):
        errors.append(err(f"{label}.reviewerNotes", "forbidden compliance language"))

    extracted = data.get("extractedAt")
    if not isinstance(extracted, str):
        errors.append(err(f"{label}.extractedAt", "required ISO 8601 string"))
    else:
        validate_iso_datetime(extracted, f"{label}.extractedAt", errors)

    # Status consistency rules
    if claim_flags and status == "draft":
        errors.append(err(f"{label}.status", "must be needs-review when any claim has reviewFlags"))
    if claim_flags and status not in {"needs-review", "rejected", "reviewer-approved"}:
        errors.append(err(f"{label}.status", "must be needs-review when any claim has reviewFlags"))
    prov_ds = prov.get("documentStatus") if isinstance(prov, dict) else None
    if prov_ds in {"superseded", "unknown"} and status == "draft":
        errors.append(err(f"{label}.status", "must be needs-review when documentStatus is superseded or unknown"))
    if "superseded" in claim_flags and status == "draft":
        errors.append(err(f"{label}.status", "must be needs-review when superseded flag present"))

    return errors


def try_jsonschema_validate(data: Any, errors: list[str]) -> None:
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return
    schema_file = schema_path()
    if not schema_file.is_file():
        return
    schema = load_json(schema_file)
    validator = jsonschema.Draft202012Validator(schema)
    for violation in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        path = ".".join(str(p) for p in violation.absolute_path) or "record"
        errors.append(err(path, violation.message))


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
        try_jsonschema_validate(data, errors)
        if errors:
            failed = True
            for line in errors:
                print(line, file=sys.stderr)
        else:
            print(f"OK: {path}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
