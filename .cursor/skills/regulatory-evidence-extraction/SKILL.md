---
name: regulatory-evidence-extraction
description: Extracts atomic, source-grounded regulatory evidence from official authority publications and approved internal controlled documents into JSON conforming to docs/schemas/evidence-record.schema.json. Use when the user explicitly invokes evidence extraction, regulatory citation harvesting, verbatim excerpt capture, or controlled-document evidence packaging — never auto-invoke.
disable-model-invocation: true
---

# Regulatory Evidence Extraction

High-risk regulated workflow. **Only run when the user explicitly invokes this skill.**

## Purpose

Extract atomic, source-grounded regulatory evidence from official and approved internal documents.

## Non-negotiable rules

- Never invent citations, quotations, regulatory requirements, dates, or sources.
- Treat **official authority publications** and **approved internal controlled documents** differently (`sourceClass`).
- Preserve: jurisdiction, issuing authority, document version, effective date, language, document status, source URL/file identifier, page, section, chunk identifier, extraction timestamp.
- Require a **verbatim evidence excerpt** for every substantive claim.
- Use status values only: `draft`, `needs-review`, `reviewer-approved`, `rejected`.
- Mark unclear, conflicting, translated, superseded, OCR-derived, or non-authoritative evidence as `needs-review` (claim `reviewFlags` + record status).
- Never declare a document, process, product, system, or submission compliant. State only evidence, coverage, gap, uncertainty, and reviewer action needed.
- Agents may set `draft` or `needs-review` only. **`reviewer-approved` is human-only.**

## Graph

```text
Source → Classify (official | internal) → Atomic claim + verbatim excerpt → Provenance → Status → Validate → JSON
```

## Workflow

```
Task Progress:
- [ ] 1. Confirm explicit user invocation and source access
- [ ] 2. Classify sourceClass
- [ ] 3. Capture provenance (all required fields)
- [ ] 4. Extract atomic claims with verbatim excerpts
- [ ] 5. Set status and reviewFlags
- [ ] 6. Write JSON file
- [ ] 7. Run validate_evidence.py — fix until exit 0
```

### Step 1 — Confirm invocation

Stop unless the user explicitly asked for evidence extraction. Do not run from ambient context.

### Step 2 — Classify source

| Source | `sourceClass` | `sourceLocator.kind` |
|--------|---------------|----------------------|
| Regulation, gazette, eCFR, EudraLex, ICH, FDA guidance URL | `official-authority` | `url` |
| Controlled SOP, policy, WI, approved validation doc | `approved-internal-controlled` | `file` |

If classification is uncertain → `needs-review` + document `uncertainties`.

### Step 3 — Provenance

Populate `provenance` before claims. Use `null` for unknown dates — never guess. See [references/evidence-schema.md](references/evidence-schema.md).

### Step 4 — Atomic claims

One claim per distinct requirement, obligation, definition, scope boundary, or gap.

- `statement`: neutral summary grounded in the excerpt
- `verbatimExcerpt`: exact quote from the source (no paraphrase, no ellipsis that hides negation)
- `excerptLocator`: page, section, chunkIdentifier (`null` when absent)

If the source does not support a requested item → add a `gap` or `uncertainty` entry; do not fabricate a claim.

### Step 5 — Status and flags

| Flag / condition | Action |
|------------------|--------|
| `unclear`, `conflicting`, `translated`, `superseded`, `ocr-derived`, `non-authoritative` | Set claim `reviewFlags`; record `status` ≥ `needs-review` |
| `documentStatus` = `superseded` or `unknown` | `needs-review` |
| First-pass agent output | `draft` or `needs-review` only |

Populate `reviewerActionNeeded` with concrete next steps (e.g. "Confirm effective date against official register").

### Step 6 — Output

Write JSON conforming to `docs/schemas/evidence-record.schema.json`.

Required envelope:

```json
{
  "schemaVersion": "maras.evidence-record.v1",
  "recordId": "EVR-YYYY-MM-DD-SOURCE-NNN",
  "status": "needs-review",
  "sourceClass": "official-authority",
  "provenance": { },
  "claims": [ ],
  "extractedAt": "YYYY-MM-DDTHH:MM:SSZ"
}
```

Optional: `coverageNotes`, `gaps`, `uncertainties`, `reviewerActionNeeded`, `reviewerNotes`.

### Step 7 — Validate

```bash
python3 .cursor/skills/regulatory-evidence-extraction/scripts/validate_evidence.py path/to/record.json
```

Fix all errors before delivering output to the user.

## Integration with MARAS

When sources overlap the app corpus:

- Reuse `GXP_CHUNKS`, `CONTROLLED_SOURCES`, and ingestion metadata patterns from `index.html`
- Align `chunkIdentifier` with existing chunk `id` when applicable (e.g. `c3`)
- Do not bypass `evaluateSourceProductionGate` semantics for licensed or held sources

## Additional resources

- Field reference and example: [references/evidence-schema.md](references/evidence-schema.md)
- Canonical JSON Schema: [docs/schemas/evidence-record.schema.json](../../../docs/schemas/evidence-record.schema.json)
