#!/usr/bin/env python3
"""Validate CTD/eCTD mapping JSON against docs/schemas/ctd-mapping-record.schema.json."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "maras.ctd-mapping.v1"
STATUSES = frozenset({"draft", "needs-review", "reviewer-approved", "rejected"})
REGIONS = frozenset({"US-FDA", "EU-EMA", "UK-MHRA", "JP-PMDA", "ICH-common", "multi-regional", "unknown"})
PRODUCT_TYPES = frozenset({"small-molecule", "biologic", "vaccine", "medical-device", "combination", "unknown"})
APP_TYPES = frozenset({"NDA", "ANDA", "BLA", "MAA", "variation", "PSUR", "DSUR", "unknown"})
MODULES = frozenset({"1", "2", "3", "4", "5", "regional-1", "unknown"})
COVERAGE = frozenset({"supports-section", "partial", "placeholder-only", "unclear", "gap"})
REVIEW_FLAGS = frozenset({
    "unclear", "conflicting", "translated", "superseded", "ocr-derived",
    "non-authoritative", "regional-mismatch", "lifecycle-uncertain",
})
RECORD_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
MAPPING_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
FORBIDDEN = re.compile(
    r"\b(compliant|non[- ]?compliant|submission[- ]?ready|inspection[- ]?ready|"
    r"dossier\s+complete|ready\s+to\s+submit|approved\s+for\s+submission)\b",
    re.IGNORECASE,
)


def schema_path() -> Path:
    return Path(__file__).resolve().parents[4] / "docs" / "schemas" / "ctd-mapping-record.schema.json"


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def err(path: str, message: str) -> str:
    return f"{path}: {message}"


def has_source_ref(refs: dict) -> bool:
    return any(refs.get(k) for k in (
        "intakeRecordId", "evidenceRecordId", "marasPbiId", "controlledDocId"
    ))


def validate_mapping(mapping: Any, path: str, errors: list[str]) -> list[str]:
    flags: list[str] = []
    if not isinstance(mapping, dict):
        errors.append(err(path, "expected object"))
        return flags
    allowed = {
        "mappingId", "ctdModule", "ctdSection", "sectionTitle", "ectdLeafTitle",
        "placementRationale", "sourceRefs", "verbatimExcerptRef", "coverageLevel",
        "reviewFlags", "reviewerActionNeeded",
    }
    extra = set(mapping) - allowed
    if extra:
        errors.append(err(path, f"unexpected fields: {sorted(extra)}"))
    for req in ("mappingId", "ctdModule", "ctdSection", "sectionTitle", "placementRationale", "sourceRefs", "coverageLevel"):
        if req not in mapping:
            errors.append(err(f"{path}.{req}", "required"))
    mid = mapping.get("mappingId")
    if isinstance(mid, str) and not MAPPING_ID.match(mid):
        errors.append(err(f"{path}.mappingId", "invalid pattern"))
    if mapping.get("ctdModule") not in MODULES:
        errors.append(err(f"{path}.ctdModule", f"must be one of {sorted(MODULES)}"))
    if mapping.get("coverageLevel") not in COVERAGE:
        errors.append(err(f"{path}.coverageLevel", f"must be one of {sorted(COVERAGE)}"))
    rationale = mapping.get("placementRationale")
    if isinstance(rationale, str) and FORBIDDEN.search(rationale):
        errors.append(err(f"{path}.placementRationale", "forbidden submission/compliance language"))
    refs = mapping.get("sourceRefs")
    if refs is not None:
        if not isinstance(refs, dict):
            errors.append(err(f"{path}.sourceRefs", "expected object"))
        elif not has_source_ref(refs):
            errors.append(err(f"{path}.sourceRefs", "at least one source ref required"))
        elif refs.get("evidenceRecordId") and not str(mapping.get("verbatimExcerptRef") or "").strip():
            errors.append(err(f"{path}.verbatimExcerptRef", "required when evidenceRecordId is set"))
    rf = mapping.get("reviewFlags") or []
    if isinstance(rf, list):
        for i, flag in enumerate(rf):
            if flag not in REVIEW_FLAGS:
                errors.append(err(f"{path}.reviewFlags[{i}]", f"unknown flag {flag!r}"))
            else:
                flags.append(flag)
    return flags


def validate_record(data: Any, *, label: str = "record") -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return [err(label, "root must be an object")]

    allowed = {
        "schemaVersion", "recordId", "status", "submissionContext", "mappings",
        "unmappedSources", "coverageNotes", "gaps", "uncertainties",
        "reviewerActionNeeded", "mappedAt",
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

    ctx = data.get("submissionContext")
    all_flags: list[str] = []
    if not isinstance(ctx, dict):
        errors.append(err(f"{label}.submissionContext", "required object"))
    else:
        if ctx.get("region") not in REGIONS:
            errors.append(err(f"{label}.submissionContext.region", f"must be one of {sorted(REGIONS)}"))
        if ctx.get("productType") not in PRODUCT_TYPES:
            errors.append(err(f"{label}.submissionContext.productType", f"must be one of {sorted(PRODUCT_TYPES)}"))
        if ctx.get("applicationType") not in APP_TYPES:
            errors.append(err(f"{label}.submissionContext.applicationType", f"must be one of {sorted(APP_TYPES)}"))

    mappings = data.get("mappings")
    seen: set[str] = set()
    if not isinstance(mappings, list):
        errors.append(err(f"{label}.mappings", "must be an array"))
    else:
        for i, m in enumerate(mappings):
            flags = validate_mapping(m, f"{label}.mappings[{i}]", errors)
            all_flags.extend(flags)
            mid = m.get("mappingId") if isinstance(m, dict) else None
            if isinstance(mid, str):
                if mid in seen:
                    errors.append(err(f"{label}.mappings[{i}].mappingId", "duplicate"))
                seen.add(mid)
        if not mappings:
            errors.append(err(f"{label}.mappings", "at least one mapping or explicit empty batch with gaps documented"))

    unmapped = data.get("unmappedSources")
    if unmapped is not None:
        if not isinstance(unmapped, list):
            errors.append(err(f"{label}.unmappedSources", "expected array"))
        else:
            for i, item in enumerate(unmapped):
                if not isinstance(item, dict) or not item.get("sourceRef") or not item.get("reason"):
                    errors.append(err(f"{label}.unmappedSources[{i}]", "requires sourceRef and reason"))

    for arr_field in ("coverageNotes", "gaps", "uncertainties", "reviewerActionNeeded"):
        val = data.get(arr_field)
        if val is None:
            continue
        if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
            errors.append(err(f"{label}.{arr_field}", "must be array of strings"))
        else:
            for i, text in enumerate(val):
                if FORBIDDEN.search(text):
                    errors.append(err(f"{label}.{arr_field}[{i}]", "forbidden submission/compliance language"))

    mapped_at = data.get("mappedAt")
    if not isinstance(mapped_at, str):
        errors.append(err(f"{label}.mappedAt", "required ISO 8601 string"))
    else:
        try:
            datetime.fromisoformat(mapped_at.replace("Z", "+00:00"))
        except ValueError:
            errors.append(err(f"{label}.mappedAt", "invalid ISO 8601 datetime"))

    if all_flags and status == "draft":
        errors.append(err(f"{label}.status", "must be needs-review when mappings have reviewFlags"))
    if isinstance(ctx, dict) and ctx.get("region") == "unknown" and status == "draft":
        errors.append(err(f"{label}.status", "must be needs-review when region is unknown"))
    if isinstance(mappings, list) and not mappings and status == "reviewer-approved":
        errors.append(err(f"{label}.status", "cannot be reviewer-approved with zero mappings and no documented waiver"))

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
