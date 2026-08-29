# Citation and provenance audit checklist

Canonical JSON Schema: [`docs/schemas/citation-provenance-audit-record.schema.json`](../../../docs/schemas/citation-provenance-audit-record.schema.json)

## Evidence record (`maras.evidence-record.v1`)

| Check | Finding category if failed |
|-------|---------------------------|
| `provenance.jurisdiction` populated | `provenance-gap` |
| `provenance.issuingAuthority` populated | `provenance-gap` |
| `provenance.sourceLocator` has `url` or `fileIdentifier` | `hash-or-locator-gap` |
| Each `claims[]` has non-empty `verbatimExcerpt` | `missing-excerpt` |
| `reviewFlags` includes `ocr-derived` when applicable | `non-authoritative-source` |
| `documentStatus: superseded` surfaced | `stale-source` |

## Intake record (`maras.source-intake.v1`)

| Check | Finding category if failed |
|-------|---------------------------|
| `original.fileHash` is 64-char hex | `hash-or-locator-gap` |
| `original.immutable: true` | `provenance-gap` |
| `metadata.documentVersion` present | `provenance-gap` |
| Downstream evidence cites matching intake id | `cross-record-conflict` |

## Comparison record (`maras.requirements-comparison.v1`)

| Check | Finding category if failed |
|-------|---------------------------|
| `sideEvidence` with `present: true` has excerpt or claim id | `missing-excerpt` |
| `citation` present when excerpt exists | `missing-citation` |
| `lexical-only` flagged when keyword match only | `unsourced-claim` |

## Change impact / authoring

| Check | Finding category if failed |
|-------|---------------------------|
| Clause deltas have supporting excerpts | `missing-excerpt` |
| `regulatoryTraceability` links have excerpt or claim id | `unsourced-claim` |
| `controls.packageStatus` is `DRAFT_NOT_CONTROLLED` | `metadata-mismatch` |

## Severity guidance

| `severity` | When |
|------------|------|
| `blocking` | Substantive claim with no excerpt and no upstream ref |
| `gap` | Missing provenance field or hash |
| `advisory` | Review flag missing but risk is indirect |
| `info` | Neutral observation for reviewer awareness |

**Never** map `info` to “acceptable for submission.”

## Minimal audit example

```json
{
  "schemaVersion": "maras.citation-provenance-audit.v1",
  "recordId": "CPA-2026-08-29-EVR-PART11",
  "status": "needs-review",
  "auditSubject": {
    "kind": "evidence-record",
    "subjectRef": "EVR-2026-08-29-PART11-0110e",
    "label": "Part 11 audit trail evidence batch"
  },
  "auditScope": [
    {
      "recordKind": "evidence-record",
      "recordId": "EVR-2026-08-29-PART11-0110e",
      "schemaVersion": "maras.evidence-record.v1"
    }
  ],
  "findings": [
    {
      "findingId": "F001",
      "category": "hash-or-locator-gap",
      "severity": "gap",
      "statement": "Evidence drawn from embedded MARAS corpus; no linked intake-record with SHA-256 for customer-controlled original.",
      "fieldPath": "provenance.sourceLocator",
      "sourceRecordId": "EVR-2026-08-29-PART11-0110e",
      "recommendation": "Link intake-record with fileHash or document corpus limitation in gaps."
    }
  ],
  "overallResult": "minor-gaps",
  "summary": {
    "findingCount": 1,
    "blockingCount": 0,
    "gapCount": 1,
    "advisoryCount": 0,
    "infoCount": 0
  },
  "controls": {
    "packageStatus": "DRAFT_NOT_CONTROLLED",
    "auditSignedOff": false
  },
  "auditedAt": "2026-08-29T18:06:00Z"
}
```
