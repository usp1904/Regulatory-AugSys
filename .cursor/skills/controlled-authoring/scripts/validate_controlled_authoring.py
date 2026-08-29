#!/usr/bin/env python3
"""Validate controlled authoring JSON against docs/schemas/controlled-authoring-record.schema.json."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "maras.controlled-authoring.v1"
STATUSES = frozenset({"draft", "needs-review", "reviewer-approved", "rejected"})
DOC_TYPES = frozenset({
    "sop", "work-instruction", "policy", "specification",
    "validation-protocol", "change-control-record", "custom",
})
PURPOSES = frozenset({"new", "revision", "obsolescence", "periodic-review", "custom"})
DOC_STATUSES = frozenset({"Draft", "Draft-For-Review", "Draft-In-Revision"})
FORBIDDEN_STATUSES = frozenset({"Effective", "Approved", "Released", "effective", "approved", "released"})
SECTION_FLAGS = frozenset({
    "machine-generated", "needs-sme-wording", "regulatory-citation-required",
    "scope-unclear", "translation-needed",
})
RECORD_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SECTION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
LINK_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
FORBIDDEN = re.compile(
    r"\b(approved\s+for\s+use|effective\s+document|released\s+to\s+production|"
    r"under\s+document\s+control|qa\s+approved|qms\s+approved|"
    r"inspection[- ]?ready|submission[- ]?ready)\b",
    re.IGNORECASE,
)


def schema_path() -> Path:
    return Path(__file__).resolve().parents[4] / "docs" / "schemas" / "controlled-authoring-record.schema.json"


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def err(path: str, message: str) -> str:
    return f"{path}: {message}"


def check_forbidden(text: str, path: str, errors: list[str]) -> None:
    if isinstance(text, str) and FORBIDDEN.search(text):
        errors.append(err(path, "forbidden approval/release language"))


def validate_record(data: Any, *, label: str = "record") -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return [err(label, "root must be an object")]

    allowed = {
        "schemaVersion", "recordId", "status", "documentType", "documentControl",
        "authoringPurpose", "changeRationale", "sections", "regulatoryTraceability",
        "upstreamRefs", "gaps", "uncertainties", "reviewerActionNeeded", "controls", "authoredAt",
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

    if data.get("documentType") not in DOC_TYPES:
        errors.append(err(f"{label}.documentType", f"must be one of {sorted(DOC_TYPES)}"))

    if data.get("authoringPurpose") not in PURPOSES:
        errors.append(err(f"{label}.authoringPurpose", f"must be one of {sorted(PURPOSES)}"))

    dc = data.get("documentControl")
    section_ids: set[str] = set()
    has_review_flags = False
    if not isinstance(dc, dict):
        errors.append(err(f"{label}.documentControl", "required object"))
    else:
        for req in ("documentId", "title", "proposedVersion", "documentStatus"):
            if not str(dc.get(req) or "").strip():
                errors.append(err(f"{label}.documentControl.{req}", "required"))
        ds = dc.get("documentStatus")
        if ds not in DOC_STATUSES:
            if str(ds) in FORBIDDEN_STATUSES:
                errors.append(err(f"{label}.documentControl.documentStatus", "agents must use draft status only"))
            else:
                errors.append(err(f"{label}.documentControl.documentStatus", f"must be one of {sorted(DOC_STATUSES)}"))

    rationale = data.get("changeRationale")
    if rationale is not None:
        check_forbidden(str(rationale), f"{label}.changeRationale", errors)

    sections = data.get("sections")
    if not isinstance(sections, list) or len(sections) < 1:
        errors.append(err(f"{label}.sections", "must be non-empty array"))
    else:
        seen_s: set[str] = set()
        for i, sec in enumerate(sections):
            if not isinstance(sec, dict):
                errors.append(err(f"{label}.sections[{i}]", "expected object"))
                continue
            sid = sec.get("sectionId")
            if not isinstance(sid, str) or not SECTION_ID.match(sid):
                errors.append(err(f"{label}.sections[{i}].sectionId", "missing or invalid"))
            elif sid in seen_s:
                errors.append(err(f"{label}.sections[{i}].sectionId", "duplicate"))
            else:
                seen_s.add(sid)
                section_ids.add(sid)
            if not str(sec.get("heading") or "").strip():
                errors.append(err(f"{label}.sections[{i}].heading", "required"))
            if not isinstance(sec.get("order"), int) or sec.get("order") < 1:
                errors.append(err(f"{label}.sections[{i}].order", "must be integer >= 1"))
            content = sec.get("content")
            if not isinstance(content, str) or not content.strip():
                errors.append(err(f"{label}.sections[{i}].content", "required"))
            else:
                check_forbidden(content, f"{label}.sections[{i}].content", errors)
            rf = sec.get("reviewFlags") or []
            if rf:
                has_review_flags = True
                for j, flag in enumerate(rf):
                    if flag not in SECTION_FLAGS:
                        errors.append(err(f"{label}.sections[{i}].reviewFlags[{j}]", f"unknown flag {flag!r}"))

    trace = data.get("regulatoryTraceability") or []
    if isinstance(trace, list):
        seen_t: set[str] = set()
        for i, link in enumerate(trace):
            if not isinstance(link, dict):
                errors.append(err(f"{label}.regulatoryTraceability[{i}]", "expected object"))
                continue
            lid = link.get("linkId")
            if not isinstance(lid, str) or not LINK_ID.match(lid):
                errors.append(err(f"{label}.regulatoryTraceability[{i}].linkId", "missing or invalid"))
            elif lid in seen_t:
                errors.append(err(f"{label}.regulatoryTraceability[{i}].linkId", "duplicate"))
            else:
                seen_t.add(lid)
            if not str(link.get("requirementRef") or "").strip():
                errors.append(err(f"{label}.regulatoryTraceability[{i}].requirementRef", "required"))
            stmt = link.get("statement")
            if not isinstance(stmt, str) or not stmt.strip():
                errors.append(err(f"{label}.regulatoryTraceability[{i}].statement", "required"))
            else:
                check_forbidden(stmt, f"{label}.regulatoryTraceability[{i}].statement", errors)
            if not str(link.get("verbatimExcerpt") or "").strip() and not str(link.get("evidenceClaimId") or "").strip():
                errors.append(err(f"{label}.regulatoryTraceability[{i}]", "verbatimExcerpt or evidenceClaimId required"))
            for j, sid in enumerate(link.get("linkedSectionIds") or []):
                if sid not in section_ids:
                    errors.append(err(f"{label}.regulatoryTraceability[{i}].linkedSectionIds[{j}]", f"unknown sectionId {sid!r}"))

    controls = data.get("controls")
    if controls is not None:
        if not isinstance(controls, dict):
            errors.append(err(f"{label}.controls", "expected object"))
        else:
            if controls.get("packageStatus") != "DRAFT_NOT_CONTROLLED":
                errors.append(err(f"{label}.controls.packageStatus", "must be DRAFT_NOT_CONTROLLED"))
            if controls.get("approvedForUse") is True:
                errors.append(err(f"{label}.controls.approvedForUse", "must be false"))
            if controls.get("effectiveInQms") is True:
                errors.append(err(f"{label}.controls.effectiveInQms", "must be false"))

    for arr_field in ("gaps", "uncertainties", "reviewerActionNeeded"):
        val = data.get(arr_field)
        if val is None:
            continue
        if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
            errors.append(err(f"{label}.{arr_field}", "must be array of strings"))

    authored = data.get("authoredAt")
    if not isinstance(authored, str):
        errors.append(err(f"{label}.authoredAt", "required ISO 8601 string"))
    else:
        try:
            datetime.fromisoformat(authored.replace("Z", "+00:00"))
        except ValueError:
            errors.append(err(f"{label}.authoredAt", "invalid ISO 8601 datetime"))

    if has_review_flags and status == "draft":
        errors.append(err(f"{label}.status", "must be needs-review when sections have reviewFlags"))

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
