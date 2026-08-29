---
name: ctd-ectd-mapper
description: Maps validated intake and evidence records to proposed ICH M4 CTD module/section and optional eCTD leaf placement in JSON conforming to docs/schemas/ctd-mapping-record.schema.json. Use when the user explicitly invokes CTD mapping, eCTD placement, dossier section routing, or RIM traceability to Module 1–5 — never auto-invoke.
disable-model-invocation: true
---

# CTD / eCTD Mapper

High-risk regulated workflow. **Only run when the user explicitly invokes this skill.**

## Purpose

Propose where sourced evidence and controlled documents may belong in an ICH M4 CTD structure (and optional regional eCTD leaf) — without asserting dossier completeness or submission readiness.

## Non-negotiable rules

- Never invent CTD sections, leaf titles, lifecycle operations, or regional requirements.
- Every mapping must trace to at least one `sourceRefs` entry (intake, evidence, PBI, or controlled doc id).
- When `evidenceRecordId` is set, `verbatimExcerptRef` is required.
- Use `coverageLevel` honestly (`partial`, `gap`, `unclear` — not `supports-section` without evidence).
- Module 1 is regional — do not harmonize across FDA/EMA/MHRA without flagging `regional-mismatch`.
- Agents may set `draft` or `needs-review` only. **`reviewer-approved` is human-only.**
- Never state that a dossier, product, or submission is complete, compliant, or ready to submit.
- Use “evidence indicates,” “gap requires review,” and “SME/QA/RA review required.”

## Graph

```text
intake (DRIVE) → evidence extraction → CTD section proposal → coverage/gap flags → Validate → JSON
                                                      ↓
                                            eCTD leaf (RA-confirmed spec only)
```

## Workflow

```
Task Progress:
- [ ] 1. Confirm explicit user invocation
- [ ] 2. Capture submissionContext (region, product, application type)
- [ ] 3. Load upstream intake/evidence records (no fabrication)
- [ ] 4. Propose mappings with placementRationale + sourceRefs
- [ ] 5. Document gaps, unmapped sources, uncertainties
- [ ] 6. Write JSON; run validate_ctd_mapping.py until exit 0
```

### Step 1 — Confirm invocation

Stop unless the user explicitly asked for CTD/eCTD mapping.

### Step 2 — Submission context

Required: `region`, `productType`, `applicationType`.

Set `ectdSpecification` and `submissionUnit` only when RA confirms — otherwise `null` and `needs-review`.

### Step 3 — Upstream inputs

Accept only:

- [`regulatory-source-intake`](../regulatory-source-intake/SKILL.md) records with `gate.decision: DRIVE` (reviewer-approved)
- [`regulatory-evidence-extraction`](../regulatory-evidence-extraction/SKILL.md) records with verbatim claims
- MARAS PBI ids and controlled doc ids supplied by the user

If upstream records are missing → list in `gaps`; do not invent evidence.

### Step 4 — Map to CTD

For each mapping:

| Field | Guidance |
|-------|----------|
| `ctdModule` | `1`–`5`, `regional-1`, or `unknown` |
| `ctdSection` | ICH M4 id (e.g. `3.2.P.5`) or regional section |
| `sectionTitle` | Standard CTD title for that section |
| `ectdLeafTitle` | Optional; only when regional spec confirmed |
| `placementRationale` | Neutral — why evidence may relate to this section |
| `coverageLevel` | See [references/ctd-ectd-structure.md](references/ctd-ectd-structure.md) |

One evidence claim may map to multiple sections only when `placementRationale` differs and flags note `regional-mismatch` or `unclear` as needed.

### Step 5 — Gaps and unmapped

- `unmappedSources`: intake/evidence/PBI refs that have no defensible CTD placement
- `gaps`: expected CTD sections with no evidenced support in this batch
- `uncertainties`: ambiguous region, product type, or eCTD spec

### Step 6 — Output and validate

```bash
python3 .cursor/skills/ctd-ectd-mapper/scripts/validate_ctd_mapping.py path/to/mapping.json
```

Required envelope:

```json
{
  "schemaVersion": "maras.ctd-mapping.v1",
  "recordId": "CTD-YYYY-MM-DD-BATCH-NNN",
  "status": "needs-review",
  "submissionContext": { "region": "US-FDA", "productType": "small-molecule", "applicationType": "NDA" },
  "mappings": [],
  "mappedAt": "YYYY-MM-DDTHH:MM:SSZ"
}
```

## MARAS integration

- RIM / Regulatory Info Mgmt system type: map validation and GxP evidence to Module 3 and regional Module 1 quality attestations when evidenced
- Reuse PBI `regRef`, `regulation`, `section` fields as mapping hints — not as automatic CTD placement
- Cross-link `marasPbiId` in `sourceRefs` when mapping assurance PBIs

## Additional resources

- CTD / eCTD structure: [references/ctd-ectd-structure.md](references/ctd-ectd-structure.md)
- JSON Schema: [docs/schemas/ctd-mapping-record.schema.json](../../../docs/schemas/ctd-mapping-record.schema.json)
- Safety rules: [`.cursor/rules/regulatory-safety.mdc`](../../../rules/regulatory-safety.mdc)
