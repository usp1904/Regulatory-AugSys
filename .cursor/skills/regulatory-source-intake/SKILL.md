---
name: regulatory-source-intake
description: Registers immutable regulatory sources and requirement files with full provenance metadata, parse status, and MARAS-aligned HOLD/DRIVE gate decisions into JSON conforming to docs/schemas/source-intake-record.schema.json. Use when the user explicitly invokes source intake, document ingestion registration, production gate evaluation, or pre-extraction source cataloguing — never auto-invoke.
disable-model-invocation: true
---

# Regulatory Source Intake

High-risk regulated workflow. **Only run when the user explicitly invokes this skill.**

## Purpose

Register immutable originals and capture metadata before parsing, chunking, embedding, or evidence extraction. Derived artifacts live separately from originals.

## Non-negotiable rules

- Never invent authority, URL, version, effective date, hash, or approval status.
- Keep **original source files immutable**; store parse text, chunks, embeddings, and summaries in separate derived artifact refs.
- Distinguish official authority, official translation, approved internal controlled, internal draft, industry commentary, and machine summaries (`sourceCategory`).
- Preserve jurisdiction, issuing authority, document class, version, document status, effective date, language, and provenance.
- Treat machine translation as non-authoritative unless an official authority translation is explicitly identified.
- Surface ambiguity, conflict, OCR uncertainty, missing metadata, and stale-document risk as `needs-review` (`reviewFlags`).
- Agents may set `draft` or `needs-review` only. **`reviewer-approved` and `gate.decision: DRIVE` are human-only** (requires `SME_APPROVED`).
- Never declare compliance, approval, or inspection-readiness. State only intake status, gate result, gaps, and reviewer action needed.
- Do not send source files or extracted text to external APIs unless data-governance policy explicitly permits it.

## Graph

```text
File → Hash → Classify → Metadata → Parse → Gate (HOLD | DRIVE) → Derived artifacts (separate)
                                      ↓
                         regulatory-evidence-extraction (DRIVE sources only)
```

## Workflow

```
Task Progress:
- [ ] 1. Confirm explicit user invocation
- [ ] 2. Hash original (SHA-256); record immutable file facts
- [ ] 3. Classify intakeKind and sourceCategory
- [ ] 4. Capture metadata (all required fields)
- [ ] 5. Parse or note parseStatus; link derivedArtifactRef only
- [ ] 6. Evaluate gate (HOLD unless human SME_APPROVED)
- [ ] 7. Write JSON; run validate_intake.py until exit 0
```

### Step 1 — Confirm invocation

Stop unless the user explicitly asked for source intake. Do not run from ambient context.

### Step 2 — Immutable original

Record `original.fileName`, `original.fileHash` (SHA-256), `original.byteSize`, `original.immutable: true`. Do not mutate the source file.

### Step 3 — Classify

| Input | `intakeKind` | Typical `sourceCategory` |
|-------|--------------|--------------------------|
| Regulation, guidance JSON, controlled source upload | `regulatory-source` | `official-authority` |
| Authority-published translation | `regulatory-source` | `official-translation` |
| Approved SOP / policy / WI | `regulatory-source` | `approved-internal-controlled` |
| Unapproved internal draft | `regulatory-source` | `internal-draft` |
| TXT/CSV/JSON requirement only | `requirement-text` | `Requirement` class in metadata |

### Step 4 — Metadata

Required: `jurisdiction`, `issuingAuthority`, `documentClass`, `documentVersion`, `language`, `documentStatus`.

Use `null` for unknown `effectiveDate` — never guess. See [references/intake-schema.md](references/intake-schema.md).

### Step 5 — Parse (derived, separate)

Set `parse.parseStatus` and `parse.derivedArtifactRef` (path/id for extracted text). Do not embed full document text in the intake record.

| `parseStatus` | When |
|---------------|------|
| `PARSED` | Text extracted successfully |
| `UNSUPPORTED_BINARY` | PDF/DOCX without parse pipeline |
| `OCR_PENDING` | Scan requires OCR verification |
| `TOO_LARGE` | Exceeds size limit |

OCR or unofficial mirror → `reviewFlags` includes `ocr-derived` or `non-authoritative`.

### Step 6 — Gate

Align with MARAS `evaluateSourceProductionGate` / `evaluateRequirementIngestionGate` in `index.html`.

| Agent default | `gate.decision` | `metadata.sourceApprovalStatus` |
|---------------|-----------------|--------------------------------|
| First pass | `HOLD` | `SME_PENDING` |
| Human approved | `DRIVE` | `SME_APPROVED` (record `status: reviewer-approved`) |

Populate `gate.missing`, `gate.reason`, `reviewerActionNeeded`.

### Step 7 — Output and validate

```bash
python3 .cursor/skills/regulatory-source-intake/scripts/validate_intake.py path/to/intake.json
```

Required envelope:

```json
{
  "schemaVersion": "maras.source-intake.v1",
  "recordId": "INT-YYYY-MM-DD-SOURCE-NNN",
  "status": "needs-review",
  "intakeKind": "regulatory-source",
  "sourceCategory": "official-authority",
  "original": { "fileName": "", "fileHash": "", "byteSize": 0, "immutable": true },
  "metadata": { },
  "gate": { "decision": "HOLD", "passed": false, "reason": "" },
  "intakeAt": "YYYY-MM-DDTHH:MM:SSZ"
}
```

## Downstream handoff

Only sources with `gate.decision: DRIVE` and `status: reviewer-approved` may feed [`regulatory-evidence-extraction`](../regulatory-evidence-extraction/SKILL.md).

## Integration with MARAS

- Mirror field names from `evaluateSourceProductionGate`, `ingestControlledSourceFile`, `ingestRequirementFile`
- Licensed sources (`LICENSE_REQUIRED`) → `gate.licenseBlocked: true`, `HOLD`
- `ingestedGenerationChunks()` includes only `DRIVE` regulatory sources

## Additional resources

- Field reference: [references/intake-schema.md](references/intake-schema.md)
- JSON Schema: [docs/schemas/source-intake-record.schema.json](../../../docs/schemas/source-intake-record.schema.json)
- Safety rules: [`.cursor/rules/regulatory-safety.mdc`](../../../rules/regulatory-safety.mdc)
