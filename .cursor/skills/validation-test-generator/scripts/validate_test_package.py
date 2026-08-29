#!/usr/bin/env python3
"""Validate validation test package JSON against docs/schemas/validation-test-package-record.schema.json."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "maras.validation-test-package.v1"
STATUSES = frozenset({"draft", "needs-review", "reviewer-approved", "rejected"})
PHASES = frozenset({"iq", "oq", "pq", "combined", "regression", "smoke", "custom"})
TEST_TYPES = frozenset({"positive", "negative", "edge-case"})
GAMP = frozenset({"1", "2", "3", "4", "5"})
COVERAGE = frozenset({"proposed", "gap", "needs-review"})
REVIEW_FLAGS = frozenset({
    "machine-generated", "needs-sme-review", "missing-negative-coverage",
    "environment-not-defined", "dual-signoff-required", "regulatory-citation-required",
})
RECORD_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
TEST_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
FORBIDDEN = re.compile(
    r"\b(validation\s+complete|all\s+tests\s+passed|system\s+validated|"
    r"qualified\s+system|iq\s+passed|oq\s+passed|pq\s+passed|"
    r"successfully\s+validated|inspection[- ]?ready)\b",
    re.IGNORECASE,
)


def schema_path() -> Path:
    return Path(__file__).resolve().parents[4] / "docs" / "schemas" / "validation-test-package-record.schema.json"


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def err(path: str, message: str) -> str:
    return f"{path}: {message}"


def check_forbidden(text: str, path: str, errors: list[str]) -> None:
    if isinstance(text, str) and FORBIDDEN.search(text):
        errors.append(err(path, "forbidden qualification/execution language"))


def validate_record(data: Any, *, label: str = "record") -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return [err(label, "root must be an object")]

    allowed = {
        "schemaVersion", "recordId", "status", "testPhase", "systemUnderTest",
        "testCases", "traceability", "environmentRequirements", "upstreamRefs",
        "summary", "gaps", "uncertainties", "reviewerActionNeeded", "controls", "generatedAt",
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

    if data.get("testPhase") not in PHASES:
        errors.append(err(f"{label}.testPhase", f"must be one of {sorted(PHASES)}"))

    sut = data.get("systemUnderTest")
    if not isinstance(sut, dict):
        errors.append(err(f"{label}.systemUnderTest", "required object"))
    else:
        if not str(sut.get("systemId") or "").strip():
            errors.append(err(f"{label}.systemUnderTest.systemId", "required"))
        if not str(sut.get("systemName") or "").strip():
            errors.append(err(f"{label}.systemUnderTest.systemName", "required"))
        gamp = sut.get("gampCategory")
        if gamp is not None and gamp not in GAMP:
            errors.append(err(f"{label}.systemUnderTest.gampCategory", f"must be one of {sorted(GAMP)}"))

    test_ids: set[str] = set()
    has_review_flags = False
    has_security_positive_only = False
    cases = data.get("testCases")
    if not isinstance(cases, list) or len(cases) < 1:
        errors.append(err(f"{label}.testCases", "must be non-empty array"))
    else:
        seen_tc: set[str] = set()
        security_positive = 0
        security_negative = 0
        for i, tc in enumerate(cases):
            if not isinstance(tc, dict):
                errors.append(err(f"{label}.testCases[{i}]", "expected object"))
                continue
            tid = tc.get("testId")
            if not isinstance(tid, str) or not TEST_ID.match(tid):
                errors.append(err(f"{label}.testCases[{i}].testId", "missing or invalid"))
            elif tid in seen_tc:
                errors.append(err(f"{label}.testCases[{i}].testId", "duplicate"))
            else:
                seen_tc.add(tid)
                test_ids.add(tid)
            if not str(tc.get("title") or "").strip():
                errors.append(err(f"{label}.testCases[{i}].title", "required"))
            obj = tc.get("objective")
            if not isinstance(obj, str) or not obj.strip():
                errors.append(err(f"{label}.testCases[{i}].objective", "required"))
            else:
                check_forbidden(obj, f"{label}.testCases[{i}].objective", errors)
            ttype = tc.get("testType")
            if ttype not in TEST_TYPES:
                errors.append(err(f"{label}.testCases[{i}].testType", f"must be one of {sorted(TEST_TYPES)}"))
            refs = tc.get("requirementRefs")
            if not isinstance(refs, list) or len(refs) < 1 or not all(isinstance(r, str) and r.strip() for r in refs):
                errors.append(err(f"{label}.testCases[{i}].requirementRefs", "must be non-empty string array"))
            steps = tc.get("steps")
            if not isinstance(steps, list) or len(steps) < 1:
                errors.append(err(f"{label}.testCases[{i}].steps", "must be non-empty array"))
            else:
                for j, step in enumerate(steps):
                    if not isinstance(step, dict):
                        errors.append(err(f"{label}.testCases[{i}].steps[{j}]", "expected object"))
                        continue
                    if not isinstance(step.get("stepNumber"), int) or step.get("stepNumber") < 1:
                        errors.append(err(f"{label}.testCases[{i}].steps[{j}].stepNumber", "must be integer >= 1"))
                    for fld in ("action", "expectedObservation"):
                        val = step.get(fld)
                        if not isinstance(val, str) or not val.strip():
                            errors.append(err(f"{label}.testCases[{i}].steps[{j}].{fld}", "required"))
                        else:
                            check_forbidden(val, f"{label}.testCases[{i}].steps[{j}].{fld}", errors)
            rf = tc.get("reviewFlags") or []
            if rf:
                has_review_flags = True
                for j, flag in enumerate(rf):
                    if flag not in REVIEW_FLAGS:
                        errors.append(err(f"{label}.testCases[{i}].reviewFlags[{j}]", f"unknown flag {flag!r}"))
            refs_text = " ".join(refs or []) if isinstance(refs, list) else ""
            if any(k in refs_text.lower() for k in ("audit", "access", "part 11", "§11")):
                if ttype == "positive":
                    security_positive += 1
                elif ttype == "negative":
                    security_negative += 1
        if security_positive > 0 and security_negative == 0:
            has_security_positive_only = True

    trace = data.get("traceability") or []
    if isinstance(trace, list):
        for i, row in enumerate(trace):
            if not isinstance(row, dict):
                errors.append(err(f"{label}.traceability[{i}]", "expected object"))
                continue
            if not str(row.get("requirementRef") or "").strip():
                errors.append(err(f"{label}.traceability[{i}].requirementRef", "required"))
            if row.get("coverageStatus") not in COVERAGE:
                errors.append(err(f"{label}.traceability[{i}].coverageStatus", f"must be one of {sorted(COVERAGE)}"))
            for j, ltid in enumerate(row.get("linkedTestIds") or []):
                if ltid not in test_ids:
                    errors.append(err(f"{label}.traceability[{i}].linkedTestIds[{j}]", f"unknown testId {ltid!r}"))

    controls = data.get("controls")
    if controls is not None:
        if not isinstance(controls, dict):
            errors.append(err(f"{label}.controls", "expected object"))
        else:
            if controls.get("packageStatus") != "DRAFT_NOT_CONTROLLED":
                errors.append(err(f"{label}.controls.packageStatus", "must be DRAFT_NOT_CONTROLLED"))
            if controls.get("executed") is True:
                errors.append(err(f"{label}.controls.executed", "must be false"))
            if controls.get("passed") is True:
                errors.append(err(f"{label}.controls.passed", "must be false"))

    for arr_field in ("gaps", "uncertainties", "reviewerActionNeeded", "environmentRequirements"):
        val = data.get(arr_field)
        if val is None:
            continue
        if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
            errors.append(err(f"{label}.{arr_field}", "must be array of strings"))

    generated = data.get("generatedAt")
    if not isinstance(generated, str):
        errors.append(err(f"{label}.generatedAt", "required ISO 8601 string"))
    else:
        try:
            datetime.fromisoformat(generated.replace("Z", "+00:00"))
        except ValueError:
            errors.append(err(f"{label}.generatedAt", "invalid ISO 8601 datetime"))

    if has_review_flags and status == "draft":
        errors.append(err(f"{label}.status", "must be needs-review when test cases have reviewFlags"))

    if has_security_positive_only and not data.get("gaps"):
        errors.append(err(f"{label}.gaps", "document missing negative test coverage for security/audit requirements"))

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
