# Evidence record schema reference

Canonical JSON Schema: [`docs/schemas/evidence-record.schema.json`](../../../docs/schemas/evidence-record.schema.json)

## Record envelope

| Field | Required | Notes |
|-------|----------|-------|
| `schemaVersion` | yes | Must be `maras.evidence-record.v1` |
| `recordId` | yes | Stable id for this extraction batch |
| `status` | yes | `draft` \| `needs-review` \| `reviewer-approved` \| `rejected` |
| `sourceClass` | yes | `official-authority` \| `approved-internal-controlled` |
| `provenance` | yes | Document-level metadata (see below) |
| `claims` | yes | ≥1 atomic claim |
| `extractedAt` | yes | ISO 8601 UTC timestamp |
| `coverageNotes` | no | Neutral scope/coverage only |
| `gaps` | no | Missing or unverified items |
| `uncertainties` | no | Ambiguity the source does not resolve |
| `reviewerActionNeeded` | no | Record-level reviewer tasks |
| `reviewerNotes` | no | Free text for reviewers |

## Source classes

### `official-authority`

Government, supranational, or officially published authority text (regulation, gazette, eCFR, EudraLex, ICH, etc.).

- `provenance.sourceLocator.kind` = `url`
- `provenance.sourceLocator.url` required
- Prefer primary publisher URL; do not substitute unofficial mirrors without `non-authoritative` flag

### `approved-internal-controlled`

Customer-controlled SOP, policy, work instruction, or validation package already under document control.

- `provenance.sourceLocator.kind` = `file`
- `provenance.sourceLocator.fileIdentifier` required (controlled doc number, hash, or repository path)
- `documentVersion` must match the controlled revision label on the document

## Provenance block

| Field | Required | Notes |
|-------|----------|-------|
| `jurisdiction` | yes | e.g. `United States`, `European Union`, `International` |
| `issuingAuthority` | yes | e.g. `US FDA / eCFR`, `European Commission` |
| `documentVersion` | yes | As stated on the source; use `unknown` only with `needs-review` |
| `effectiveDate` | no | `YYYY-MM-DD` or `null` if not stated |
| `language` | yes | BCP 47 or plain label, e.g. `en`, `en-US` |
| `documentStatus` | yes | `current` \| `superseded` \| `draft` \| `unknown` |
| `sourceLocator` | yes | URL or file pointer + optional page/section/chunk |

## Claim object

Each substantive regulatory statement is **one claim** with its own verbatim excerpt.

| Field | Required | Notes |
|-------|----------|-------|
| `claimId` | yes | Unique within record |
| `claimType` | yes | See enum in schema |
| `statement` | yes | Short neutral summary — **not** a compliance conclusion |
| `verbatimExcerpt` | yes | Exact quote; must appear in source |
| `excerptLocator` | yes | `page`, `section`, `chunkIdentifier` (use `null` when absent) |
| `reviewFlags` | no | Triggers `needs-review` when present |
| `reviewerActionNeeded` | no | Per-claim reviewer task |

## Status rules

| Condition | Minimum record `status` |
|-----------|-------------------------|
| Any claim has `reviewFlags` | `needs-review` |
| `documentStatus` = `superseded` or `unknown` | `needs-review` |
| Missing `effectiveDate` when date is material | `needs-review` |
| OCR-only text without human verification | `needs-review` + flag `ocr-derived` |
| Translation not from official source | `needs-review` + flag `translated` |
| Conflicting passages in same batch | `needs-review` + flag `conflicting` |
| Human reviewer signs off | `reviewer-approved` (never set by the agent alone) |
| Evidence rejected as unusable | `rejected` |

Agents may output `draft` or `needs-review` only. **`reviewer-approved` requires a human reviewer.**

## Forbidden language

Do **not** use in `statement`, `coverageNotes`, `gaps`, or `uncertainties`:

- compliant / non-compliant / in compliance
- approved / certification / cleared / validated (as a product/system conclusion)
- submission-ready / inspection-ready (as conclusions)

Allowed: *"The source states …"*, *"Coverage for §X is not evidenced in the provided excerpt"*, *"Reviewer should confirm effective date"*.

## Minimal example

```json
{
  "schemaVersion": "maras.evidence-record.v1",
  "recordId": "EVR-2026-08-29-PART11-001",
  "status": "needs-review",
  "sourceClass": "official-authority",
  "provenance": {
    "jurisdiction": "United States",
    "issuingAuthority": "US FDA / eCFR",
    "documentVersion": "Current eCFR",
    "effectiveDate": null,
    "language": "en",
    "documentStatus": "current",
    "sourceLocator": {
      "kind": "url",
      "url": "https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11",
      "page": null,
      "section": "§11.10(e)",
      "chunkIdentifier": "c3"
    }
  },
  "claims": [
    {
      "claimId": "C001",
      "claimType": "requirement",
      "statement": "The source requires secure, computer-generated, time-stamped audit trails for operator entries and actions.",
      "verbatimExcerpt": "Use of secure, computer-generated, time-stamped audit trails to independently record the date and time of operator entries and actions.",
      "excerptLocator": {
        "page": null,
        "section": "§11.10(e)",
        "chunkIdentifier": "c3"
      },
      "reviewFlags": [],
      "reviewerActionNeeded": "Confirm eCFR capture date matches customer baseline."
    }
  ],
  "coverageNotes": ["Excerpt addresses audit trail controls only; signature manifestations not included."],
  "gaps": ["§11.50 not extracted in this batch."],
  "uncertainties": [],
  "reviewerActionNeeded": ["SME confirm jurisdiction applicability for non-US sites."],
  "extractedAt": "2026-08-29T17:30:00Z"
}
```

## Validation

```bash
python3 .cursor/skills/regulatory-evidence-extraction/scripts/validate_evidence.py path/to/record.json
```

Exit `0` = valid. Non-zero = errors printed to stderr.
