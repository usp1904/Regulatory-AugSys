---
name: data-integrity-checker
description: Assesses regulatory records and artifacts against ALCOA+ data integrity principles (attributable, legible, contemporaneous, original, accurate, complete, consistent, enduring, available) into JSON conforming to docs/schemas/data-integrity-assessment-record.schema.json. Use when the user explicitly invokes data integrity checking, ALCOA+ review, provenance validation, or metadata gap analysis — never auto-invoke.
disable-model-invocation: true
---

# Data Integrity Checker

High-risk regulated workflow. **Only run when the user explicitly invokes this skill.**

## Purpose

Assess whether a sourced record or artifact supports ALCOA+ data integrity expectations for metadata, provenance, and lineage — without certifying compliance.

## Non-negotiable rules

- Never invent metadata, hashes, timestamps, or source facts.
- Never state that data, systems, or records are ALCOA+ compliant or data-integrity certified.
- Evaluate only from supplied upstream JSON or verified MARAS fields — not assumptions.
- Flag OCR, translation, corpus-copy, and missing-hash conditions as `needs-review`.
- Original files stay immutable; derived parse/chunk/summary must be assessed separately (`derivedSeparated`).
- Agents may set `draft` or `needs-review` only. **`reviewer-approved` is human-only.**
- Use “evidence indicates,” “gap requires review,” and “SME/QA review required.”

## Graph

```text
Upstream record → ALCOA+ principle scan → Risk rating → Gaps → Validate → JSON
```

## Workflow

```
Task Progress:
- [ ] 1. Confirm explicit user invocation
- [ ] 2. Load assessmentSubject (kind + subjectRef)
- [ ] 3. Score ALCOA+ principles (pass | fail | needs-review | na)
- [ ] 4. Set overallRisk from principle results
- [ ] 5. Document gaps, uncertainties, reviewerActionNeeded
- [ ] 6. Write JSON; run validate_data_integrity.py until exit 0
```

### Step 1 — Confirm invocation

Stop unless the user explicitly asked for data integrity or ALCOA+ assessment.

### Step 2 — Subject kinds

| `kind` | Upstream |
|--------|----------|
| `evidence-record` | `regulatory-evidence-extraction` |
| `intake-record` | `regulatory-source-intake` |
| `comparison-record` | `requirements-comparator` |
| `document-review-record` | `regulated-document-review` |
| `maras-pbi` | MARAS story / export row |
| `derived-artifact` | Parse/chunk/embed summary file |

See [references/alcoa-assessment.md](references/alcoa-assessment.md) for per-principle checks.

### Step 3 — ALCOA+ principles

Include at least **five** principles; prefer **all nine** when data allows.

| Principle | Quick check |
|-----------|-------------|
| `attributable` | Authority, jurisdiction, reviewer/source identity |
| `legible` | Verbatim excerpts readable |
| `contemporaneous` | Timestamps on extract/intake/assess |
| `original` | Immutable original vs derivative separation |
| `accurate` | No fabricated citations or requirements |
| `complete` | Required schema fields present |
| `consistent` | No cross-field conflicts |
| `enduring` | Version, effective date, document status |
| `available` | URL or controlled file id for retrieval |

### Step 4 — Overall risk

| Condition | `overallRisk` |
|-----------|---------------|
| `fail` on attributable, original, or accurate | `high` |
| Any other `fail` or core `needs-review` | `medium` |
| Only `pass` / `na` | `low` (rare — default `needs-review` status) |
| Insufficient input | `unknown` |

### Step 5 — Controls

```json
"controls": {
  "originalImmutable": true,
  "derivedSeparated": true,
  "packageStatus": "DRAFT_NOT_CONTROLLED"
}
```

Use `null` when not assessable from supplied data.

### Step 6 — Validate

```bash
python3 .cursor/skills/data-integrity-checker/scripts/validate_data_integrity.py path/to/assessment.json
```

Required envelope:

```json
{
  "schemaVersion": "maras.data-integrity-assessment.v1",
  "recordId": "DIA-YYYY-MM-DD-SUBJECT",
  "status": "needs-review",
  "assessmentSubject": { "kind": "evidence-record", "subjectRef": "" },
  "principles": [],
  "overallRisk": "unknown",
  "assessedAt": "YYYY-MM-DDTHH:MM:SSZ"
}
```

## MARAS integration

- Cross-check `GXP_CHUNKS` c6 (FDA DI / ALCOA) when topic is data integrity
- Intake: verify `original.immutable` and `fileHash` via `regulatory-source-intake`
- Global Compare topic `data-integrity` for cross-market context only — not automatic pass

## Downstream

Feed gaps into [`regulated-document-review`](../regulated-document-review/SKILL.md) findings or [`requirements-comparator`](../requirements-comparator/SKILL.md) when SOP vs regulation conflicts involve record integrity.

## Additional resources

- ALCOA+ reference: [references/alcoa-assessment.md](references/alcoa-assessment.md)
- JSON Schema: [docs/schemas/data-integrity-assessment-record.schema.json](../../../docs/schemas/data-integrity-assessment-record.schema.json)
- Safety rules: [`.cursor/rules/regulatory-safety.mdc`](../../../rules/regulatory-safety.mdc)
