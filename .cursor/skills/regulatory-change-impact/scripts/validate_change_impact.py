#!/usr/bin/env python3
"""Validate regulatory change impact JSON against docs/schemas/regulatory-change-impact-record.schema.json."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "maras.regulatory-change-impact.v1"
STATUSES = frozenset({"draft", "needs-review", "reviewer-approved", "rejected"})
CHANGE_TYPES = frozenset({
    "version-amendment", "new-publication", "withdrawal",
    "effective-date-shift", "scope-clarification", "custom",
})
CHANGE_KINDS = frozenset({"added", "removed", "modified", "relocated", "superseded", "unclear"})
IMPACT_LEVELS = frozenset({"high", "medium", "low", "unknown"})
ASSET_KINDS = frozenset({
    "system", "sop", "pbi", "test-case", "evidence-record",
    "validation-package", "controlled-document", "ctd-module", "custom",
})
CLAUSE_FLAGS = frozenset({
    "unclear", "translated", "superseded", "ocr-derived", "non-authoritative",
    "scope-mismatch", "effective-date-unverified",
})
ASSET_FLAGS = frozenset({
    "inferred-link", "lexical-only", "scope-mismatch", "stale-artifact", "missing-owner",
})
RECORD_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
CHANGE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
ASSET_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
FORBIDDEN = re.compile(
    r"\b(change\s+control\s+(complete|closed)|remediation\s+(complete|done)|"
    r"no\s+impact\s+confirmed|remains?\s+compliant|post[- ]change\s+compliant|"
    r"fully\s+remediated|inspection[- ]?ready\s+after\s+change)\b",
    re.IGNORECASE,
)


def schema_path() -> Path:
    return Path(__file__).resolve().parents[4] / "docs" / "schemas" / "regulatory-change-impact-record.schema.json"


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def err(path: str, message: str) -> str:
    return f"{path}: {message}"


def check_forbidden(text: str, path: str, errors: list[str]) -> None:
    if isinstance(text, str) and FORBIDDEN.search(text):
        errors.append(err(path, "forbidden closure/compliance language"))


def validate_clause_change(cc: Any, path: str, errors: list[str]) -> tuple[str | None, list[str]]:
    flags: list[str] = []
    if not isinstance(cc, dict):
        errors.append(err(path, "expected object"))
        return None, flags
    allowed = {
        "changeId", "clauseRef", "changeKind", "statement",
        "beforeExcerpt", "afterExcerpt", "evidenceClaimId", "reviewFlags",
    }
    extra = set(cc) - allowed
    if extra:
        errors.append(err(path, f"unexpected fields: {sorted(extra)}"))
    cid = cc.get("changeId")
    if not isinstance(cid, str) or not CHANGE_ID.match(cid):
        errors.append(err(f"{path}.changeId", "missing or invalid"))
    if not str(cc.get("clauseRef") or "").strip():
        errors.append(err(f"{path}.clauseRef", "required"))
    kind = cc.get("changeKind")
    if kind not in CHANGE_KINDS:
        errors.append(err(f"{path}.changeKind", f"must be one of {sorted(CHANGE_KINDS)}"))
    stmt = cc.get("statement")
    if not isinstance(stmt, str) or not stmt.strip():
        errors.append(err(f"{path}.statement", "required"))
    else:
        check_forbidden(stmt, f"{path}.statement", errors)
    before = str(cc.get("beforeExcerpt") or "").strip()
    after = str(cc.get("afterExcerpt") or "").strip()
    claim = str(cc.get("evidenceClaimId") or "").strip()
    if kind == "modified":
        if not before and not after and not claim:
            errors.append(err(path, "modified requires beforeExcerpt/afterExcerpt or evidenceClaimId"))
    if kind == "added" and not after and not claim:
        errors.append(err(path, "added requires afterExcerpt or evidenceClaimId"))
    if kind == "removed" and not before and not claim:
        errors.append(err(path, "removed requires beforeExcerpt or evidenceClaimId"))
    rf = cc.get("reviewFlags") or []
    if isinstance(rf, list):
        for i, flag in enumerate(rf):
            if flag not in CLAUSE_FLAGS:
                errors.append(err(f"{path}.reviewFlags[{i}]", f"unknown flag {flag!r}"))
            else:
                flags.append(flag)
    return cid if isinstance(cid, str) else None, flags


def validate_impacted_asset(asset: Any, path: str, change_ids: set[str], errors: list[str]) -> list[str]:
    flags: list[str] = []
    if not isinstance(asset, dict):
        errors.append(err(path, "expected object"))
        return flags
    allowed = {
        "assetId", "assetKind", "assetRef", "label", "impactLevel",
        "rationale", "linkedClauseChangeIds", "reviewFlags",
    }
    extra = set(asset) - allowed
    if extra:
        errors.append(err(path, f"unexpected fields: {sorted(extra)}"))
    aid = asset.get("assetId")
    if not isinstance(aid, str) or not ASSET_ID.match(aid):
        errors.append(err(f"{path}.assetId", "missing or invalid"))
    if asset.get("assetKind") not in ASSET_KINDS:
        errors.append(err(f"{path}.assetKind", f"must be one of {sorted(ASSET_KINDS)}"))
    if not str(asset.get("assetRef") or "").strip():
        errors.append(err(f"{path}.assetRef", "required"))
    if asset.get("impactLevel") not in IMPACT_LEVELS:
        errors.append(err(f"{path}.impactLevel", f"must be one of {sorted(IMPACT_LEVELS)}"))
    rationale = asset.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        errors.append(err(f"{path}.rationale", "required"))
    else:
        check_forbidden(rationale, f"{path}.rationale", errors)
    linked = asset.get("linkedClauseChangeIds") or []
    if isinstance(linked, list):
        for i, lid in enumerate(linked):
            if lid not in change_ids:
                errors.append(err(f"{path}.linkedClauseChangeIds[{i}]", f"unknown changeId {lid!r}"))
    rf = asset.get("reviewFlags") or []
    if isinstance(rf, list):
        for i, flag in enumerate(rf):
            if flag not in ASSET_FLAGS:
                errors.append(err(f"{path}.reviewFlags[{i}]", f"unknown flag {flag!r}"))
            else:
                flags.append(flag)
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

    if data.get("changeType") not in CHANGE_TYPES:
        errors.append(err(f"{label}.changeType", f"must be one of {sorted(CHANGE_TYPES)}"))

    cs = data.get("changeSource")
    if not isinstance(cs, dict):
        errors.append(err(f"{label}.changeSource", "required object"))
    else:
        if not str(cs.get("authority") or "").strip():
            errors.append(err(f"{label}.changeSource.authority", "required"))
        if not str(cs.get("documentTitle") or "").strip():
            errors.append(err(f"{label}.changeSource.documentTitle", "required"))

    summary_text = data.get("changeSummary")
    if summary_text is not None:
        check_forbidden(str(summary_text), f"{label}.changeSummary", errors)

    change_ids: set[str] = set()
    clause_flags: list[str] = []
    clause_changes = data.get("clauseChanges")
    if not isinstance(clause_changes, list) or len(clause_changes) < 1:
        errors.append(err(f"{label}.clauseChanges", "must be non-empty array"))
    else:
        seen_cc: set[str] = set()
        for i, cc in enumerate(clause_changes):
            cid, flags = validate_clause_change(cc, f"{label}.clauseChanges[{i}]", errors)
            clause_flags.extend(flags)
            if cid:
                if cid in seen_cc:
                    errors.append(err(f"{label}.clauseChanges[{i}].changeId", "duplicate"))
                seen_cc.add(cid)
                change_ids.add(cid)

    asset_flags: list[str] = []
    high_count = 0
    assets = data.get("impactedAssets")
    if assets is None:
        assets = []
    if not isinstance(assets, list):
        errors.append(err(f"{label}.impactedAssets", "must be array"))
    else:
        seen_ia: set[str] = set()
        for i, asset in enumerate(assets):
            flags = validate_impacted_asset(asset, f"{label}.impactedAssets[{i}]", change_ids, errors)
            asset_flags.extend(flags)
            if isinstance(asset, dict):
                if asset.get("impactLevel") == "high":
                    high_count += 1
                iid = asset.get("assetId")
                if isinstance(iid, str):
                    if iid in seen_ia:
                        errors.append(err(f"{label}.impactedAssets[{i}].assetId", "duplicate"))
                    seen_ia.add(iid)

    for arr_field in ("recommendedActions", "gaps", "uncertainties", "reviewerActionNeeded"):
        val = data.get(arr_field)
        if val is None:
            continue
        if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
            errors.append(err(f"{label}.{arr_field}", "must be array of strings"))
        else:
            for i, text in enumerate(val):
                check_forbidden(text, f"{label}.{arr_field}[{i}]", errors)

    controls = data.get("controls")
    if controls is not None:
        if not isinstance(controls, dict):
            errors.append(err(f"{label}.controls", "expected object"))
        elif controls.get("packageStatus") != "DRAFT_NOT_CONTROLLED":
            errors.append(err(f"{label}.controls.packageStatus", "must be DRAFT_NOT_CONTROLLED"))
        if isinstance(controls, dict) and controls.get("changeControlClosed") is True:
            errors.append(err(f"{label}.controls.changeControlClosed", "agents must not set changeControlClosed=true"))

    assessed = data.get("assessedAt")
    if not isinstance(assessed, str):
        errors.append(err(f"{label}.assessedAt", "required ISO 8601 string"))
    else:
        try:
            datetime.fromisoformat(assessed.replace("Z", "+00:00"))
        except ValueError:
            errors.append(err(f"{label}.assessedAt", "invalid ISO 8601 datetime"))

    needs_review = bool(clause_flags) or bool(asset_flags) or high_count > 0
    has_unclear = isinstance(clause_changes, list) and any(
        isinstance(cc, dict) and cc.get("changeKind") == "unclear" for cc in clause_changes
    )
    if (needs_review or has_unclear) and status == "draft":
        errors.append(err(f"{label}.status", "must be needs-review when review flags, high impact, or unclear changes present"))

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
