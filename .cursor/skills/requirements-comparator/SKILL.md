---
name: requirements-comparator
description: Compares two or more sourced requirement sets (cross-market, SOP vs regulation, version diff, PBI vs source) with verbatim excerpts and relationship classification into JSON conforming to docs/schemas/requirements-comparison-record.schema.json. Use when the user explicitly invokes requirements comparison, gap analysis across sources, or Global Compare-style matrix work — never auto-invoke.
disable-model-invocation: true
---

# Requirements Comparator

High-risk regulated workflow. **Only run when the user explicitly invokes this skill.**

## Purpose

Compare requirement sets side-by-side with citations and neutral difference statements — without harmonisation, gap-closure, or compliance conclusions.

## Non-negotiable rules

- Never invent citations, excerpts, requirements, or source versions.
- Every `present: true` side requires `verbatimExcerpt` or `evidenceClaimId` from upstream extraction.
- Classify each item: `aligned` | `divergent` | `gap-left` | `gap-right` | `conflict` | `unclear`.
- Keyword-only matches → `reviewFlags: ["lexical-only"]` and `needs-review`.
- Never state that requirements are harmonised, compliant, or submission-ready.
- Use “evidence indicates,” “gap requires review,” “difference noted,” and “SME/QA/RA review required.”
- Agents may set `draft` or `needs-review` only. **`reviewer-approved` is human-only.**

## Graph

```text
Evidence (both sides) → Topic align → Relationship → Differences → Gaps/uncovered → Validate → JSON
```

## Workflow

```
Task Progress:
- [ ] 1. Confirm explicit user invocation
- [ ] 2. Define comparisonType and sides (2–6)
- [ ] 3. Load upstream evidence/intake (no fabrication)
- [ ] 4. Build comparison items with sideEvidence
- [ ] 5. Summarise counts, gaps, uncovered topics
- [ ] 6. Write JSON; run validate_comparison.py until exit 0
```

### Step 1 — Confirm invocation

Stop unless the user explicitly asked for requirements comparison.

### Step 2 — Define sides

| Field | Required |
|-------|----------|
| `sideId` | Short id (`US`, `EU`, `SOP-A`, `v2`) |
| `label` | Human-readable label with authority |
| `jurisdiction` | When applicable |
| `sourceRefs` | intake / evidence / chunk / topic ids |

Order matters for `gap-left` / `gap-right` (first side = left).

### Step 3 — Upstream inputs

Prefer [`regulatory-evidence-extraction`](../regulatory-evidence-extraction/SKILL.md) records. For MARAS corpus, cite `marasChunkId` and excerpts from `GXP_CHUNKS`.

For SOP comparison, reuse `mapSopToRegulations()` semantics — flag lexical-only matches.

### Step 4 — Comparison items

One row per topic or requirement theme:

- `statement`: neutral summary of what the comparison shows
- `sideEvidence[]`: per-side citation + excerpt
- `differences[]`: bullet deltas (required for `divergent` and `conflict`)
- `relationship: conflict` → record `status` ≥ `needs-review`

### Step 5 — Summary

Populate `summary` counts and list `uncoveredTopics` / `gaps` for markets or sources not in batch.

### Step 6 — Output and validate

```bash
python3 .cursor/skills/requirements-comparator/scripts/validate_comparison.py path/to/comparison.json
```

Required envelope:

```json
{
  "schemaVersion": "maras.requirements-comparison.v1",
  "recordId": "CMP-YYYY-MM-DD-TOPIC",
  "status": "needs-review",
  "comparisonType": "cross-market",
  "sides": [],
  "items": [],
  "comparedAt": "YYYY-MM-DDTHH:MM:SSZ"
}
```

## MARAS integration

- **Global Compare**: align `globalCompareTopicId` with `GLOBAL_COMPARE_TOPICS`; use `diffMarketCells` pattern for pairwise `differences`
- **Readiness / SOP mapper**: `sop-vs-regulation` type; surface `conflicts` like `SOP_CONFLICT_RULES`
- **Assure PBIs**: `pbi-vs-source` — compare PBI `story`/`ac` to `regRef` excerpt

## Downstream

Comparison output may inform [`ctd-ectd-mapper`](../ctd-ectd-mapper/SKILL.md) gap notes — not automatic CTD placement.

## Additional resources

- Field reference: [references/comparison-schema.md](references/comparison-schema.md)
- JSON Schema: [docs/schemas/requirements-comparison-record.schema.json](../../../docs/schemas/requirements-comparison-record.schema.json)
- Safety rules: [`.cursor/rules/regulatory-safety.mdc`](../../../rules/regulatory-safety.mdc)
