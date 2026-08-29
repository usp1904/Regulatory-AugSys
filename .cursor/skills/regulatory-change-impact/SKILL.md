---
name: regulatory-change-impact
description: Assesses regulatory source changes (version amendments, new publications, withdrawals, effective-date shifts) and maps potential downstream impact on systems, SOPs, PBIs, tests, and evidence into JSON conforming to docs/schemas/regulatory-change-impact-record.schema.json. Use when the user explicitly invokes regulatory change impact analysis, source diffing, or change-package scoping — never auto-invoke.
disable-model-invocation: true
---

# Regulatory Change Impact

High-risk regulated workflow. **Only run when the user explicitly invokes this skill.**

## Purpose

Trace a sourced regulatory change to potentially impacted clauses and downstream artifacts — without closing change control or certifying remediation.

## Non-negotiable rules

- Never invent source versions, effective dates, clause text, or artifact links.
- Every `modified` / `added` / `removed` clause change requires supporting excerpts or upstream evidence refs.
- Asset impact links are hypotheses until SME/QA/RA review — flag `inferred-link` or `lexical-only` when appropriate.
- Never state that change control is complete, remediation is done, or systems remain compliant after the change.
- Use “evidence indicates,” “may require review,” “potential impact,” and “SME/QA/RA review required.”
- Agents may set `draft` or `needs-review` only. **`reviewer-approved` is human-only.**

## Graph

```text
Source change (before/after) → Clause deltas → Asset linkage → Recommended actions → Validate → JSON
```

## Workflow

```
Task Progress:
- [ ] 1. Confirm explicit user invocation
- [ ] 2. Define changeType and changeSource (before/after)
- [ ] 3. Document clauseChanges with excerpts or evidence refs
- [ ] 4. Map impactedAssets with impactLevel and rationale
- [ ] 5. List recommendedActions, gaps, uncertainties
- [ ] 6. Write JSON; run validate_change_impact.py until exit 0
```

### Step 1 — Confirm invocation

Stop unless the user explicitly asked for regulatory change impact analysis.

### Step 2 — Change types

| `changeType` | Use when |
|--------------|----------|
| `version-amendment` | Official revision of an existing instrument |
| `new-publication` | First-time publication affecting scope |
| `withdrawal` | Source or clause retired |
| `effective-date-shift` | Same text, new applicability window |
| `scope-clarification` | Interpretive/guidance clarification |
| `custom` | User-defined — document in `uncertainties` |

Populate `changeSource.before` and `changeSource.after` with version labels, effective dates, and upstream intake/evidence ids when available.

### Step 3 — Upstream inputs

Prefer in order:

1. [`requirements-comparator`](../requirements-comparator/SKILL.md) with `comparisonType: version-diff`
2. Paired [`regulatory-evidence-extraction`](../regulatory-evidence-extraction/SKILL.md) records (before/after)
3. [`regulatory-source-intake`](../regulatory-source-intake/SKILL.md) for immutable originals and hashes

Set `upstreamRefs.comparisonRecordId` when a version-diff comparison exists.

### Step 4 — Clause changes

One row per clause or section delta:

| `changeKind` | Excerpt rule |
|--------------|--------------|
| `modified` | `beforeExcerpt` and `afterExcerpt` required unless `unclear` |
| `added` | `afterExcerpt` required |
| `removed` | `beforeExcerpt` required |
| `unclear` | No fabricated text; flag `unclear` or `effective-date-unverified` |

### Step 5 — Impacted assets

Map systems, SOPs, PBIs, tests, evidence, validation packages, or CTD modules:

| `impactLevel` | Guidance |
|---------------|----------|
| `high` | Direct clause citation on asset or explicit traceability link |
| `medium` | Thematic overlap with review flags |
| `low` | Peripheral or administrative touch |
| `unknown` | Insufficient linkage data |

Link assets to clause changes via `linkedClauseChangeIds` when evidenced.

### Step 6 — Validate

```bash
python3 .cursor/skills/regulatory-change-impact/scripts/validate_change_impact.py path/to/impact.json
```

Required envelope:

```json
{
  "schemaVersion": "maras.regulatory-change-impact.v1",
  "recordId": "RCI-YYYY-MM-DD-TOPIC",
  "status": "needs-review",
  "changeType": "version-amendment",
  "changeSource": {
    "authority": "",
    "documentTitle": "",
    "before": {},
    "after": {}
  },
  "clauseChanges": [],
  "impactedAssets": [],
  "assessedAt": "YYYY-MM-DDTHH:MM:SSZ"
}
```

## MARAS integration

- Assurance scenario: source update → impacted clauses → systems/PBIs/tests/SOPs → change package delta
- Reuse `version-diff` comparisons and MARAS PBI `req_id` / `source` traceability for `assetRef`
- Readiness / SOP mapper: flag SOP assets when regulation deltas overlap mapped controls
- Do not claim live source monitoring — batch assessment only

## Downstream

Impact records may inform [`regulated-document-review`](../regulated-document-review/SKILL.md), [`ctd-ectd-mapper`](../ctd-ectd-mapper/SKILL.md) gap notes, and [`data-integrity-checker`](../data-integrity-checker/SKILL.md) provenance checks.

## Additional resources

- Field reference: [references/impact-schema.md](references/impact-schema.md)
- JSON Schema: [docs/schemas/regulatory-change-impact-record.schema.json](../../../docs/schemas/regulatory-change-impact-record.schema.json)
- Safety rules: [`.cursor/rules/regulatory-safety.mdc`](../../../rules/regulatory-safety.mdc)
