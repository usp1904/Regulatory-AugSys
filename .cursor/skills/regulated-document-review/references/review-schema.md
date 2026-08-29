# Document review record reference

Canonical JSON Schema: [`docs/schemas/document-review-record.schema.json`](../../../docs/schemas/document-review-record.schema.json)

## Purpose

Prepare or record a **draft** SME/QA/RA review worksheet for regulated content. This is **not** electronic signature, regulatory approval, or a controlled QMS record.

## Review decisions (MARAS-aligned)

| `reviewDecision` | Meaning |
|------------------|---------|
| `NOT_REVIEWED` | Agent-prepared worksheet; no human attestation yet |
| `NEEDS_SECOND_REVIEW` | First reviewer flagged; second qualified reviewer required |
| `CLARIFICATION_REQUIRED` | Maps to MARAS `CLARIFICATION_REQUIRED` on PBI cards |
| `SME_REVIEW_ATTESTED_DRAFT` | Human attested draft review in session — **not approval** |
| `REJECTED` | Content unusable until remediated |

## Agent vs human

| Action | Who |
|--------|-----|
| Prepare checklist, findings, gaps | Agent (status `needs-review`) |
| Set `SME_REVIEW_ATTESTED_DRAFT` | **Human only** — requires `reviewer.name`, `reviewer.role`, `reviewer.comment` |
| Set `reviewer-approved` on record | **Human only** |
| Invent reviewer identity | **Never** |

## Mandatory controls

```json
"controls": {
  "electronicSignature": false,
  "immutableAuditRecord": false,
  "packageStatus": "DRAFT_NOT_CONTROLLED"
}
```

`evidenceReadiness.submissionReady` must always be `false` in agent output.

## Default checklist (adapt per subject)

| id | label |
|----|-------|
| `source_trace` | Citations trace to authoritative or controlled sources |
| `verbatim` | Substantive claims have verbatim excerpts |
| `version` | Document version and effective date confirmed |
| `jurisdiction` | Jurisdiction applicability confirmed |
| `license` | Licensed sources have documented entitlement |
| `conflict` | No unresolved conflicts between sources |
| `watermark` | Exports remain `DRAFT_NOT_CONTROLLED` |

## Subject kinds

| `reviewSubject.kind` | Typical upstream |
|----------------------|----------------|
| `evidence-record` | `regulatory-evidence-extraction` |
| `intake-record` | `regulatory-source-intake` |
| `comparison-record` | `requirements-comparator` |
| `ctd-mapping-record` | `ctd-ectd-mapper` |
| `maras-pbi-package` | MARAS Assure output |
| `inspection-pack` | Readiness tab pack |
| `controlled-document` | Customer SOP/WI id |

## Minimal example (worksheet — not attested)

```json
{
  "schemaVersion": "maras.document-review.v1",
  "recordId": "REV-2026-08-29-EVR-PART11",
  "status": "needs-review",
  "reviewSubject": {
    "kind": "evidence-record",
    "subjectRef": "EVR-2026-08-29-PART11-0110e",
    "label": "21 CFR Part 11 §11.10(e) audit trail evidence"
  },
  "reviewer": null,
  "reviewDecision": "NOT_REVIEWED",
  "checklist": [
    { "id": "source_trace", "label": "Citations trace to authoritative sources", "result": "needs-review", "evidence": "officialUrl present; SME_PENDING on PART11 corpus" },
    { "id": "verbatim", "label": "Substantive claims have verbatim excerpts", "result": "pass", "evidence": "3 claims with verbatimExcerpt" },
    { "id": "watermark", "label": "Draft watermark preserved", "result": "pass", "evidence": "DRAFT_NOT_CONTROLLED" }
  ],
  "findings": [
    {
      "findingId": "F001",
      "severity": "advisory",
      "statement": "Evidence indicates excerpts were taken from MARAS embedded corpus; gap requires review against live eCFR.",
      "citationRef": "EVR-2026-08-29-PART11-0110e",
      "verbatimExcerptRef": null
    }
  ],
  "gaps": ["§11.50 not covered in evidence batch"],
  "uncertainties": ["Jurisdiction applicability for EU-only sites not assessed"],
  "reviewerActionNeeded": ["Qualified SME verify verbatim text against eCFR baseline"],
  "evidenceReadiness": {
    "decision": "NOT_READY",
    "score": 0,
    "submissionReady": false
  },
  "controls": {
    "electronicSignature": false,
    "immutableAuditRecord": false,
    "packageStatus": "DRAFT_NOT_CONTROLLED"
  },
  "preparedAt": "2026-08-29T17:54:00Z"
}
```

## Validation

```bash
python3 .cursor/skills/regulated-document-review/scripts/validate_review.py path/to/review.json
```
