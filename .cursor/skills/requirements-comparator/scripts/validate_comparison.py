#!/usr/bin/env python3
"""Validate requirements comparison JSON against docs/schemas/requirements-comparison-record.schema.json."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "maras.requirements-comparison.v1"
STATUSES = frozenset({"draft", "needs-review", "reviewer-approved", "rejected"})
COMP_TYPES = frozenset({
    "cross-market", "sop-vs-regulation", "version-diff",
    "pbi-vs-source", "internal-vs-authority", "custom",
})
RELATIONSHIPS = frozenset({"aligned", "divergent", "gap-left", "gap-right", "conflict", "unclear"})
REVIEW_FLAGS = frozenset({
    "unclear", "conflicting", "translated", "superseded", "ocr-derived",
    "non-authoritative", "lexical-only", "scope-mismatch",
})
RECORD_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
ITEM_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
SIDE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$")
FORBIDDEN = re.compile(
    r"\b(compliant|non[- ]?compliant|harmonised?\s+for\s+submission|"
    r"submission[- ]?ready|inspection[- ]?ready|fully\s+aligned\s+with\s+regulation)\b",
    re.IGNORECASE,
)


def schema_path() -> Path:
    return Path(__file__).resolve().parents[4] / "docs" / "schemas" / "requirements-comparison-record.schema.json"


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def err(path: str, message: str) -> str:
    return f"{path}: {message}"


def validate_side_evidence(ev: Any, path: str, errors: list[str]) -> None:
    if not isinstance(ev, dict):
        errors.append(err(path, "expected object"))
        return
    if ev.get("present") is True:
        if not str(ev.get("verbatimExcerpt") or "").strip() and not str(ev.get("evidenceClaimId") or "").strip():
            errors.append(err(path, "verbatimExcerpt or evidenceClaimId required when present=true"))


def validate_item(item: Any, path: str, side_ids: set[str], errors: list[str]) -> list[str]:
    flags: list[str] = []
    if not isinstance(item, dict):
        errors.append(err(path, "expected object"))
        return flags
    allowed = {
        "itemId", "topic", "relationship", "statement", "sideEvidence",
        "differences", "reviewFlags", "reviewerActionNeeded",
    }
    extra = set(item) - allowed
    if extra:
        errors.append(err(path, f"unexpected fields: {sorted(extra)}"))
    for req in ("itemId", "topic", "relationship", "statement"):
        if req not in item:
            errors.append(err(f"{path}.{req}", "required"))
    if item.get("relationship") not in RELATIONSHIPS:
        errors.append(err(f"{path}.relationship", f"must be one of {sorted(RELATIONSHIPS)}"))
    stmt = item.get("statement")
    if isinstance(stmt, str) and FORBIDDEN.search(stmt):
        errors.append(err(f"{path}.statement", "forbidden compliance/harmonisation language"))
    se = item.get("sideEvidence")
    if se is not None:
        if not isinstance(se, list) or len(se) < 1:
            errors.append(err(f"{path}.sideEvidence", "must be non-empty array"))
        else:
            seen_sides: set[str] = set()
            for i, ev in enumerate(se):
                validate_side_evidence(ev, f"{path}.sideEvidence[{i}]", errors)
                if isinstance(ev, dict):
                    sid = ev.get("sideId")
                    if sid not in side_ids:
                        errors.append(err(f"{path}.sideEvidence[{i}].sideId", f"unknown side {sid!r}"))
                    if sid in seen_sides:
                        errors.append(err(f"{path}.sideEvidence[{i}].sideId", "duplicate sideId"))
                    seen_sides.add(sid)
    rel = item.get("relationship")
    if rel in {"gap-left", "gap-right", "conflict", "unclear"} and item.get("status") == "draft":
        pass  # status is on record not item
    rf = item.get("reviewFlags") or []
    if isinstance(rf, list):
        for i, flag in enumerate(rf):
            if flag not in REVIEW_FLAGS:
                errors.append(err(f"{path}.reviewFlags[{i}]", f"unknown flag {flag!r}"))
            else:
                flags.append(flag)
    if rel == "aligned" and not item.get("differences") and flags:
        pass
    return flags


def validate_record(data: Any, *, label: str = "record") -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return [err(label, "root must be an object")]

    if data.get("schemaVersion") != SCHEMA_VERSION:
        errors.append(err(f"{label}.schemaVersion", f"must be {SCHEMA_VERSION!r}"))

    rid = data.get("recordId")
    if not isinstance(rid, str) or not RECORD_ID.match(rid):
        errors.append(err(f"{label}.recordId", "missing or invalid"))

    status = data.get("status")
    if status not in STATUSES:
        errors.append(err(f"{label}.status", f"must be one of {sorted(STATUSES)}"))

    if data.get("comparisonType") not in COMP_TYPES:
        errors.append(err(f"{label}.comparisonType", f"must be one of {sorted(COMP_TYPES)}"))

    sides = data.get("sides")
    side_ids: set[str] = set()
    if not isinstance(sides, list) or len(sides) < 2:
        errors.append(err(f"{label}.sides", "must have 2–6 sides"))
    else:
        for i, side in enumerate(sides):
            if not isinstance(side, dict):
                errors.append(err(f"{label}.sides[{i}]", "expected object"))
                continue
            sid = side.get("sideId")
            if not isinstance(sid, str) or not SIDE_ID.match(sid):
                errors.append(err(f"{label}.sides[{i}].sideId", "invalid"))
            elif sid in side_ids:
                errors.append(err(f"{label}.sides[{i}].sideId", "duplicate"))
            else:
                side_ids.add(sid)
            if not str(side.get("label") or "").strip():
                errors.append(err(f"{label}.sides[{i}].label", "required"))

    all_flags: list[str] = []
    items = data.get("items")
    if not isinstance(items, list) or len(items) < 1:
        errors.append(err(f"{label}.items", "must be non-empty array"))
    else:
        seen_items: set[str] = set()
        for i, item in enumerate(items):
            flags = validate_item(item, f"{label}.items[{i}]", side_ids, errors)
            all_flags.extend(flags)
            iid = item.get("itemId") if isinstance(item, dict) else None
            if isinstance(iid, str):
                if iid in seen_items:
                    errors.append(err(f"{label}.items[{i}].itemId", "duplicate"))
                seen_items.add(iid)

    for arr_field in ("uncoveredTopics", "gaps", "uncertainties", "reviewerActionNeeded"):
        val = data.get(arr_field)
        if val is None:
            continue
        if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
            errors.append(err(f"{label}.{arr_field}", "must be array of strings"))
        else:
            for i, text in enumerate(val):
                if FORBIDDEN.search(text):
                    errors.append(err(f"{label}.{arr_field}[{i}]", "forbidden language"))

    compared = data.get("comparedAt")
    if not isinstance(compared, str):
        errors.append(err(f"{label}.comparedAt", "required ISO 8601 string"))
    else:
        try:
            datetime.fromisoformat(compared.replace("Z", "+00:00"))
        except ValueError:
            errors.append(err(f"{label}.comparedAt", "invalid ISO 8601 datetime"))

    if all_flags and status == "draft":
        errors.append(err(f"{label}.status", "must be needs-review when items have reviewFlags"))

    has_conflict = isinstance(items, list) and any(
        isinstance(it, dict) and it.get("relationship") == "conflict" for it in items
    )
    if has_conflict and status == "draft":
        errors.append(err(f"{label}.status", "must be needs-review when any item relationship is conflict"))

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
