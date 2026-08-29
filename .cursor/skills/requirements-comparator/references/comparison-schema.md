# Requirements comparison reference

Canonical JSON Schema: [`docs/schemas/requirements-comparison-record.schema.json`](../../../docs/schemas/requirements-comparison-record.schema.json)

## Comparison types

| `comparisonType` | Use when |
|------------------|----------|
| `cross-market` | Same topic across jurisdictions (MARAS Global Compare pattern) |
| `sop-vs-regulation` | Client SOP/policy vs regulatory source |
| `version-diff` | Document revision A vs B |
| `pbi-vs-source` | MARAS PBI vs cited regulation |
| `internal-vs-authority` | Controlled internal doc vs official authority text |
| `custom` | User-defined — document rationale in `uncertainties` |

## Relationship values

| `relationship` | Meaning |
|----------------|---------|
| `aligned` | Substantive requirement language appears consistent across sides |
| `divergent` | Both sides address topic but material differences exist |
| `gap-left` | Topic evidenced on right side only (first side in `sides` is “left”) |
| `gap-right` | Topic evidenced on left side only |
| `conflict` | Sides appear incompatible — SME review required |
| `unclear` | Insufficient excerpt or scope to compare |

**Never** map `aligned` to “compliant” or “harmonised for submission.”

## Side evidence rules

Each `comparisonItem` should include `sideEvidence` for every compared side:

- `present: true` → `verbatimExcerpt` **or** `evidenceClaimId` required
- `present: false` → no invented excerpt; use `gap-left` / `gap-right`
- Keyword-only matches → flag `lexical-only` and `needs-review`

## MARAS integration

| MARAS feature | Comparator bridge |
|---------------|-------------------|
| `GLOBAL_COMPARE_TOPICS` | `sourceRefs.globalCompareTopicId` + chunk ids in side evidence |
| `mapSopToRegulations()` | `sop-vs-regulation`; reuse overlap/gap/conflict semantics |
| `diffMarketCells()` | `differences[]` per item for pairwise market deltas |
| Evidence records | `evidenceClaimId` + `verbatimExcerpt` from upstream extraction |

## Minimal example (cross-market)

```json
{
  "schemaVersion": "maras.requirements-comparison.v1",
  "recordId": "CMP-2026-08-29-AUDIT-TRAIL",
  "status": "needs-review",
  "comparisonType": "cross-market",
  "sides": [
    {
      "sideId": "US",
      "label": "United States (21 CFR Part 11)",
      "jurisdiction": "United States",
      "sourceRefs": { "marasChunkId": "c3", "globalCompareTopicId": "audit-trail" }
    },
    {
      "sideId": "EU",
      "label": "European Union (Annex 11)",
      "jurisdiction": "European Union",
      "sourceRefs": { "marasChunkId": "c4", "globalCompareTopicId": "audit-trail" }
    }
  ],
  "items": [
    {
      "itemId": "I001",
      "topic": "Audit trail for record changes",
      "relationship": "divergent",
      "statement": "Evidence indicates both markets require audit trails for GxP-critical changes; US text emphasises operator entries and independent timestamps while EU Annex 11 frames traceability to the individual.",
      "sideEvidence": [
        {
          "sideId": "US",
          "present": true,
          "citation": "21 CFR Part 11 §11.10(e)",
          "verbatimExcerpt": "Use of secure, computer-generated, time-stamped audit trails to independently record the date and time of operator entries and actions.",
          "evidenceClaimId": "C001",
          "section": "§11.10(e)"
        },
        {
          "sideId": "EU",
          "present": true,
          "citation": "EU GMP Annex 11 Cl.10",
          "verbatimExcerpt": "Relevant changes to GxP critical data should be recorded and traceable to the person who made the change.",
          "evidenceClaimId": null,
          "section": "Cl.10"
        }
      ],
      "differences": [
        "US: explicit operator-entry wording and independent audit trail",
        "EU: individual traceability framing"
      ],
      "reviewFlags": [],
      "reviewerActionNeeded": "SME confirm excerpts against current official sources."
    }
  ],
  "summary": {
    "alignedCount": 0,
    "divergentCount": 1,
    "gapCount": 0,
    "conflictCount": 0,
    "unclearCount": 0
  },
  "uncoveredTopics": ["e-signature manifestations"],
  "gaps": ["UK MHRA not included in this batch"],
  "uncertainties": [],
  "reviewerActionNeeded": ["RA/QA review required before using in client deliverables."],
  "comparedAt": "2026-08-29T17:52:00Z"
}
```

## Validation

```bash
python3 .cursor/skills/requirements-comparator/scripts/validate_comparison.py path/to/comparison.json
```

## Upstream skills

- [`regulatory-evidence-extraction`](../regulatory-evidence-extraction/SKILL.md) — verbatim excerpts required
- [`regulatory-source-intake`](../regulatory-source-intake/SKILL.md) — DRIVE sources only
