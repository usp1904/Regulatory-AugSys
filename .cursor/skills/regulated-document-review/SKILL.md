---
name: regulated-document-review
description: Prepares or records structured SME/QA/RA review worksheets for evidence, intake, comparison, CTD mapping, and MARAS packages in JSON conforming to docs/schemas/document-review-record.schema.json. Use when the user explicitly invokes regulated document review, draft attestation, inspection readiness review, or qualified reviewer sign-off preparation — never auto-invoke.
disable-model-invocation: true
---

# Regulated Document Review

High-risk regulated workflow. **Only run when the user explicitly invokes this skill.**

## Purpose

Prepare a structured review worksheet or record a **draft** human attestation for regulated content — without electronic signature, regulatory approval, or controlled-record claims.

## Non-negotiable rules

- Never invent reviewer name, role, comment, or review timestamp.
- Never set `electronicSignature: true` or `submissionReady: true`.
- Always set `controls.packageStatus` to `DRAFT_NOT_CONTROLLED`.
- Agents prepare worksheets with `reviewDecision: NOT_REVIEWED` and `status: needs-review`.
- `SME_REVIEW_ATTESTED_DRAFT` requires human-supplied `reviewer.name`, `reviewer.role`, and `reviewer.comment` — never fabricate.
- `reviewer-approved` on the record is **human-only**.
- Never state that a product, dossier, process, system, site, or document is compliant, approved, validated, or inspection-ready.
- Use “evidence indicates,” “gap requires review,” and “SME/QA/RA review required.”

## Graph

```text
Upstream record → Checklist → Findings → Readiness (NOT_READY default) → Human attestation (optional) → Validate → JSON
```

## Workflow

```
Task Progress:
- [ ] 1. Confirm explicit user invocation
- [ ] 2. Identify reviewSubject (kind + subjectRef)
- [ ] 3. Run default checklist against upstream record
- [ ] 4. Document findings, gaps, uncertainties
- [ ] 5. Set evidenceReadiness (submissionReady: false)
- [ ] 6. Record human attestation only if user provided reviewer fields
- [ ] 7. Write JSON; run validate_review.py until exit 0
```

### Step 1 — Confirm invocation

Stop unless the user explicitly asked for document review or attestation recording.

### Step 2 — Review subject

| `kind` | Upstream skill / artifact |
|--------|---------------------------|
| `evidence-record` | `regulatory-evidence-extraction` |
| `intake-record` | `regulatory-source-intake` |
| `comparison-record` | `requirements-comparator` |
| `ctd-mapping-record` | `ctd-ectd-mapper` |
| `maras-pbi-package` | MARAS Assure / `allStories` |
| `inspection-pack` | `buildInspectionReadinessPack` |
| `controlled-document` | Customer doc id |

### Step 3 — Checklist

Use default items from [references/review-schema.md](references/review-schema.md). Mark `needs-review` when upstream status is `needs-review` or `SME_PENDING`.

### Step 4 — Findings

| `severity` | When |
|------------|------|
| `info` | Neutral observation |
| `advisory` | Review recommended |
| `gap` | Missing expected evidence |
| `blocking` | Prevents draft attestation until resolved |

Each finding needs `statement`; link `citationRef` / `verbatimExcerptRef` when available.

### Step 5 — Evidence readiness

Default agent output:

```json
"evidenceReadiness": {
  "decision": "NOT_READY",
  "score": 0,
  "submissionReady": false
}
```

Use `CONDITIONALLY_READY` only when user’s qualified reviewer explicitly requests it and blockers are documented.

### Step 6 — Human attestation (optional)

Only when the user provides reviewer identity and comment:

```json
"reviewer": {
  "name": "<from user>",
  "role": "<from user>",
  "comment": "<from user>",
  "reviewedAt": "<ISO 8601 from user or system clock at attestation>"
},
"reviewDecision": "SME_REVIEW_ATTESTED_DRAFT"
```

Maps to MARAS PBI `SME_REVIEW_ATTESTED_DRAFT` — still **not** regulatory approval.

### Step 7 — Validate

```bash
python3 .cursor/skills/regulated-document-review/scripts/validate_review.py path/to/review.json
```

Required envelope:

```json
{
  "schemaVersion": "maras.document-review.v1",
  "recordId": "REV-YYYY-MM-DD-SUBJECT",
  "status": "needs-review",
  "reviewSubject": { "kind": "evidence-record", "subjectRef": "" },
  "reviewDecision": "NOT_REVIEWED",
  "checklist": [],
  "preparedAt": "YYYY-MM-DDTHH:MM:SSZ"
}
```

## MARAS integration

- Mirror `markFtr()` requirements: attestation needs name, role, and comment
- Align `evidenceReadiness.decision` with `H.review.evidence_decision` (`NOT_READY` until human process completes)
- Exports must remain `DRAFT_NOT_CONTROLLED` (MVP-10, MVP-12)

## Additional resources

- Field reference: [references/review-schema.md](references/review-schema.md)
- JSON Schema: [docs/schemas/document-review-record.schema.json](../../../docs/schemas/document-review-record.schema.json)
- Safety rules: [`.cursor/rules/regulatory-safety.mdc`](../../../rules/regulatory-safety.mdc)
