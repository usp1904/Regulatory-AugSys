# Data integrity assessment reference

Canonical JSON Schema: [`docs/schemas/data-integrity-assessment-record.schema.json`](../../../docs/schemas/data-integrity-assessment-record.schema.json)

## ALCOA+ principles

| `principle` | Check focus |
|-------------|-------------|
| `attributable` | Source, author, reviewer, jurisdiction, authority identifiable |
| `legible` | Records readable; excerpts preserved verbatim |
| `contemporaneous` | `extractedAt` / `intakeAt` / capture timestamps present |
| `original` | Immutable original separated from derived parse/chunk/summary |
| `accurate` | No invented citations, dates, or requirements |
| `complete` | Required schema fields populated; no silent omissions |
| `consistent` | No conflicting metadata across linked records |
| `enduring` | Version, effective date, document status captured |
| `available` | Source locator (URL/file id) enables retrieval |

Use `na` only when the principle does not apply to the subject kind.

## Result values

| `result` | Meaning |
|----------|---------|
| `pass` | Evidence indicates the principle is met for this assessment scope |
| `fail` | Material gap observed |
| `needs-review` | Ambiguous, OCR, translation, or SME confirmation required |
| `na` | Not applicable |

**Never** map `pass` to “ALCOA+ compliant” or “data integrity certified.”

## Subject kinds

| `kind` | Typical checks |
|--------|----------------|
| `evidence-record` | Verbatim excerpts, provenance, reviewFlags |
| `intake-record` | `original.immutable`, hash, gate metadata |
| `comparison-record` | Both sides cited; lexical-only flagged |
| `maras-pbi` | `regRef`, source URL, reviewer fields |
| `derived-artifact` | Must not overwrite original; lineage to intake |

## Overall risk

| `overallRisk` | Guidance |
|---------------|----------|
| `low` | No `fail`; at most advisory `needs-review` |
| `medium` | Any `needs-review` on core principles (attributable, original, accurate) |
| `high` | Any `fail` on attributable, original, or accurate |
| `unknown` | Insufficient subject data to assess |

Agents default to `needs-review` status and `overallRisk: unknown` when inputs are incomplete.

## Minimal example

```json
{
  "schemaVersion": "maras.data-integrity-assessment.v1",
  "recordId": "DIA-2026-08-29-EVR-PART11",
  "status": "needs-review",
  "assessmentSubject": {
    "kind": "evidence-record",
    "subjectRef": "EVR-2026-08-29-PART11-0110e",
    "label": "Part 11 audit trail evidence batch"
  },
  "principles": [
    {
      "principle": "attributable",
      "result": "needs-review",
      "statement": "Issuing authority and jurisdiction are recorded; SME approval on source corpus is still pending.",
      "evidenceRef": "provenance.issuingAuthority",
      "gap": "sourceApprovalStatus not SME_APPROVED"
    },
    {
      "principle": "legible",
      "result": "pass",
      "statement": "Claims include verbatim excerpts in readable text.",
      "evidenceRef": "claims[].verbatimExcerpt",
      "gap": null
    },
    {
      "principle": "contemporaneous",
      "result": "pass",
      "statement": "extractedAt timestamp is present.",
      "evidenceRef": "extractedAt",
      "gap": null
    },
    {
      "principle": "original",
      "result": "needs-review",
      "statement": "Evidence drawn from embedded MARAS corpus rather than customer-controlled original file hash in this batch.",
      "evidenceRef": "coverageNotes",
      "gap": "Link to intake-record with fileHash recommended"
    },
    {
      "principle": "accurate",
      "result": "needs-review",
      "statement": "Excerpts require verification against live eCFR before reliance.",
      "evidenceRef": "reviewerActionNeeded",
      "gap": null
    }
  ],
  "overallRisk": "medium",
  "gaps": ["No linked intake-record with SHA-256 for original source file"],
  "uncertainties": ["Whether corpus text matches current eCFR"],
  "reviewerActionNeeded": ["QA verify ALCOA attributable and accurate principles against official source"],
  "controls": {
    "originalImmutable": null,
    "derivedSeparated": true,
    "packageStatus": "DRAFT_NOT_CONTROLLED"
  },
  "assessedAt": "2026-08-29T17:59:00Z"
}
```

## Validation

```bash
python3 .cursor/skills/data-integrity-checker/scripts/validate_data_integrity.py path/to/assessment.json
```

## Pipeline position

```text
intake → evidence → data-integrity-checker → compare / review / CTD
```
