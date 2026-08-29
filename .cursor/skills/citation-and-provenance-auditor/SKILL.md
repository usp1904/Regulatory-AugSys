---
name: citation-and-provenance-auditor
description: Audits citations, verbatim excerpts, and provenance metadata across regulatory JSON records (evidence, intake, comparison, change impact, authoring, document review) into JSON conforming to docs/schemas/citation-provenance-audit-record.schema.json. Use when the user explicitly invokes citation audit, provenance verification, traceability review, or source-grounding checks — never auto-invoke.
disable-model-invocation: true
---

# Citation and Provenance Auditor

High-risk regulated workflow. **Only run when the user explicitly invokes this skill.**

## Purpose

Audit whether upstream regulatory JSON artifacts support their citations and provenance claims — without certifying audit pass, full traceability, or regulatory compliance.

## Non-negotiable rules

- Never invent citations, excerpts, hashes, URLs, versions, or audit conclusions.
- Audit only records supplied in `auditScope` — do not assume unseen upstream data.
- Every substantive claim in scoped records must trace to `verbatimExcerpt`, `evidenceClaimId`, or intake `fileHash` / `sourceLocator`.
- Flag `non-authoritative-source`, `stale-source`, and `metadata-mismatch` when evidence indicates risk.
- Never state that citations are certified, provenance is verified, or the package is fully traceable.
- Use “evidence indicates,” “gap requires review,” and “SME/QA/RA review required.”
- Agents may set `draft` or `needs-review` only. **`reviewer-approved` is human-only.**

## Graph

```text
Scoped records → Citation scan → Provenance scan → Cross-record check → Findings → Validate → JSON
```

## Workflow

```
Task Progress:
- [ ] 1. Confirm explicit user invocation
- [ ] 2. Define auditSubject and auditScope (record ids)
- [ ] 3. Check excerpts, citations, provenance fields per record kind
- [ ] 4. Cross-check jurisdiction, version, authority across scope
- [ ] 5. Document findings with category and severity
- [ ] 6. Set overallResult; run validate_citation_audit.py until exit 0
```

### Step 1 — Confirm invocation

Stop unless the user explicitly asked for citation or provenance audit.

### Step 2 — Audit scope

List every record examined:

```json
{ "recordKind": "evidence-record", "recordId": "EVR-...", "schemaVersion": "maras.evidence-record.v1" }
```

For batch audits use `auditSubject.kind: multi-record-batch`.

### Step 3 — Per-record checks

| Record kind | Primary checks |
|-------------|----------------|
| `evidence-record` | Each claim has `verbatimExcerpt`; provenance complete; `reviewFlags` surfaced |
| `intake-record` | `original.fileHash`; metadata; `gate.decision` vs downstream use |
| `comparison-record` | `present: true` sides have excerpt or `evidenceClaimId` |
| `change-impact-record` | Clause excerpts for `modified`/`added`/`removed` |
| `authoring-record` | `regulatoryTraceability` sourced; draft controls intact |
| `document-review-record` | Findings link `citationRef` when citing evidence |

See [references/audit-checklist.md](references/audit-checklist.md).

### Step 4 — Finding categories

| `category` | When |
|------------|------|
| `missing-excerpt` | Substantive claim without verbatim text |
| `missing-citation` | Reference without clause/section locator |
| `provenance-gap` | Required provenance field null or absent |
| `metadata-mismatch` | Jurisdiction/authority/version conflict across scope |
| `unsourced-claim` | Statement not linked to scoped evidence |
| `stale-source` | `documentStatus: superseded` or unverified effective date |
| `non-authoritative-source` | Machine summary or OCR without flag |
| `cross-record-conflict` | Incompatible values between scoped records |
| `hash-or-locator-gap` | No file hash or URL for retrieval |
| `scope-mismatch` | Citation outside stated jurisdiction/scope |

### Step 5 — Overall result

| Condition | `overallResult` |
|-----------|-----------------|
| Any `blocking` finding | `major-gaps` |
| `gap` findings only | `minor-gaps` or `needs-review` |
| Only `info`/`advisory` | `needs-review` (default for agent output) |
| Insufficient scope | `inconclusive` |

### Step 6 — Validate

```bash
python3 .cursor/skills/citation-and-provenance-auditor/scripts/validate_citation_audit.py path/to/audit.json
```

Required envelope:

```json
{
  "schemaVersion": "maras.citation-provenance-audit.v1",
  "recordId": "CPA-YYYY-MM-DD-SUBJECT",
  "status": "needs-review",
  "auditSubject": { "kind": "evidence-record", "subjectRef": "" },
  "auditScope": [],
  "findings": [],
  "overallResult": "needs-review",
  "auditedAt": "YYYY-MM-DDTHH:MM:SSZ"
}
```

## MARAS integration

- Mirror `scoreValidationRubric` traceability expectations: unsourced PBI claims → `unsourced-claim`
- `CONTROLLED_SOURCES` / `GXP_CHUNKS`: note corpus-copy vs customer hash in `hash-or-locator-gap`
- Complements [`data-integrity-checker`](../data-integrity-checker/SKILL.md) (ALCOA+) with citation-focused depth

## Downstream

Audit findings may feed [`regulated-document-review`](../regulated-document-review/SKILL.md) worksheets or [`controlled-authoring`](../controlled-authoring/SKILL.md) revision notes.

## Additional resources

- Checklist: [references/audit-checklist.md](references/audit-checklist.md)
- JSON Schema: [docs/schemas/citation-provenance-audit-record.schema.json](../../../docs/schemas/citation-provenance-audit-record.schema.json)
- Safety rules: [`.cursor/rules/regulatory-safety.mdc`](../../../rules/regulatory-safety.mdc)
