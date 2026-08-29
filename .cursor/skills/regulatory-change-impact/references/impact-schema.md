# Regulatory change impact reference

Canonical JSON Schema: [`docs/schemas/regulatory-change-impact-record.schema.json`](../../../docs/schemas/regulatory-change-impact-record.schema.json)

## Change types

| `changeType` | Use when |
|--------------|----------|
| `version-amendment` | Official revision of an existing regulation or guidance |
| `new-publication` | New instrument affecting in-scope processes |
| `withdrawal` | Retired source or clause |
| `effective-date-shift` | Applicability window changes without substantive text delta |
| `scope-clarification` | Interpretive update — often `needs-review` |
| `custom` | User-defined — document rationale in `uncertainties` |

## Clause change kinds

| `changeKind` | Excerpt expectations |
|--------------|------------------------|
| `modified` | `beforeExcerpt` + `afterExcerpt` unless `unclear` |
| `added` | `afterExcerpt` |
| `removed` | `beforeExcerpt` |
| `relocated` | Both excerpts or citation refs when text unchanged |
| `superseded` | Link to replacement in `statement` |
| `unclear` | No invented text; use `reviewFlags` |

## Asset kinds

| `assetKind` | Typical `assetRef` |
|-------------|-------------------|
| `system` | Application or platform id |
| `sop` | Controlled document id |
| `pbi` | MARAS story id or ADO work item |
| `test-case` | Test script or protocol id |
| `evidence-record` | Upstream evidence record id |
| `validation-package` | IQ/OQ/PQ package id |
| `controlled-document` | Policy or specification id |
| `ctd-module` | CTD section reference |
| `custom` | User-defined — explain in `label` |

## Impact levels

| `impactLevel` | Meaning |
|---------------|---------|
| `high` | Direct traceability or cited clause on asset |
| `medium` | Thematic overlap — SME confirmation required |
| `low` | Peripheral touch |
| `unknown` | Linkage not evidenced |

**Never** map `low` to “no action required” or “compliant.”

## Review flags

**Clause changes:** `unclear`, `translated`, `superseded`, `ocr-derived`, `non-authoritative`, `scope-mismatch`, `effective-date-unverified`

**Impacted assets:** `inferred-link`, `lexical-only`, `scope-mismatch`, `stale-artifact`, `missing-owner`

## MARAS integration

| MARAS feature | Impact bridge |
|---------------|---------------|
| Assurance scenario “Regulatory change impact” | Clause → PBI/test/SOP linkage pattern |
| `requirements-comparator` `version-diff` | `upstreamRefs.comparisonRecordId` |
| PBI `req_id` / `source` | `assetKind: pbi` with story id |
| `mapSopToRegulations()` | `assetKind: sop` when SOP maps to changed clause |

## Minimal example

```json
{
  "schemaVersion": "maras.regulatory-change-impact.v1",
  "recordId": "RCI-2026-08-29-ANNEX11-AUDIT",
  "status": "needs-review",
  "changeType": "version-amendment",
  "changeSource": {
    "authority": "European Commission / EMA",
    "jurisdiction": "European Union",
    "documentTitle": "EU GMP Annex 11",
    "before": { "versionLabel": "Rev. prior", "effectiveDate": null },
    "after": { "versionLabel": "Rev. draft-not-verified", "effectiveDate": null }
  },
  "clauseChanges": [
    {
      "changeId": "CC001",
      "clauseRef": "Annex 11 Cl.10",
      "changeKind": "modified",
      "statement": "Evidence indicates audit-trail review frequency language may have changed.",
      "beforeExcerpt": "Prior text not verified in this batch.",
      "afterExcerpt": "Relevant changes to GxP critical data should be recorded and traceable.",
      "reviewFlags": ["effective-date-unverified"]
    }
  ],
  "impactedAssets": [
    {
      "assetId": "IA001",
      "assetKind": "pbi",
      "assetRef": "STORY-AUDIT-TRAIL-001",
      "impactLevel": "medium",
      "rationale": "PBI cites Annex 11 audit-trail controls; clause delta may affect acceptance criteria.",
      "linkedClauseChangeIds": ["CC001"],
      "reviewFlags": ["inferred-link"]
    }
  ],
  "assessedAt": "2026-08-29T18:01:00Z"
}
```
