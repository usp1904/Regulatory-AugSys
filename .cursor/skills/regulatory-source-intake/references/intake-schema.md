# Source intake record reference

Canonical JSON Schema: [`docs/schemas/source-intake-record.schema.json`](../../../docs/schemas/source-intake-record.schema.json)

## Purpose

Register an **immutable original** and its metadata before parsing, chunking, embedding, or evidence extraction. Derived artifacts are stored separately — never overwrite the original.

## Graph

```text
File → Hash → Classify → Metadata → Parse → Gate (HOLD | DRIVE) → Derived artifacts (separate)
```

Downstream: [`regulatory-evidence-extraction`](../regulatory-evidence-extraction/SKILL.md) consumes **DRIVE** sources only.

## Source categories

| `sourceCategory` | Use when |
|------------------|----------|
| `official-authority` | Regulation, gazette, eCFR, EudraLex, ICH primary publication |
| `official-translation` | Authority-published translation explicitly identified |
| `approved-internal-controlled` | Customer SOP/policy/WI under document control |
| `internal-draft` | Unapproved internal draft |
| `industry-commentary` | ISPE, consultant white papers, non-authoritative interpretation |
| `machine-summary` | LLM or automated summary — never authoritative |

Machine translation without official authority identification → `reviewFlags: ["translated", "non-authoritative"]` and `needs-review`.

## MARAS gate alignment (`evaluateSourceProductionGate`)

Regulatory-source **DRIVE** requires all of:

- `officialUrl` (valid https URL)
- `authority`, `documentClass`, `effectiveDate`, `capturedAt`
- `fileHash` (SHA-256, 64 hex)
- `licenseTag` present; not `LICENSE_REQUIRED` unless licensed
- `sourceApprovalStatus` = `SME_APPROVED`
- `parseStatus` = `PARSED` with excerpt

Agents must **not** set `SME_APPROVED` or `gate.decision: DRIVE` without human sign-off. Default agent output: `status: needs-review`, `gate.decision: HOLD`.

Requirement-text intake (`intakeKind: requirement-text`) follows `evaluateRequirementIngestionGate`: txt/csv/json only, parsed non-empty text, valid hash, size within limit.

## Minimal example (HOLD — pending SME)

```json
{
  "schemaVersion": "maras.source-intake.v1",
  "recordId": "INT-2026-08-29-PART11-json",
  "status": "needs-review",
  "intakeKind": "regulatory-source",
  "sourceCategory": "official-authority",
  "original": {
    "fileName": "part11-source.json",
    "fileHash": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
    "byteSize": 2048,
    "mimeType": "application/json",
    "immutable": true
  },
  "metadata": {
    "jurisdiction": "United States",
    "issuingAuthority": "US FDA / eCFR",
    "documentClass": "Regulation",
    "documentVersion": "Current eCFR",
    "effectiveDate": "1997-08-20",
    "officialUrl": "https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11",
    "controlledDocId": null,
    "licenseTag": "PUBLIC_US_GOVERNMENT",
    "sourceApprovalStatus": "SME_PENDING",
    "language": "en",
    "documentStatus": "current"
  },
  "parse": {
    "parseStatus": "PARSED",
    "capturedAt": "2026-08-29",
    "derivedArtifactRef": "derived/part11-source.parse.txt"
  },
  "gate": {
    "decision": "HOLD",
    "passed": false,
    "missing": ["sourceApprovalStatus"],
    "licenseBlocked": false,
    "reason": "sourceApprovalStatus"
  },
  "reviewFlags": [],
  "uncertainties": [],
  "reviewerActionNeeded": ["SME/QA/RA review required: approve source before DRIVE."],
  "intakeAt": "2026-08-29T17:49:00Z"
}
```

## Validation

```bash
python3 .cursor/skills/regulatory-source-intake/scripts/validate_intake.py path/to/intake.json
```
