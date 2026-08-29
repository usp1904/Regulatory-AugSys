# CTD / eCTD structure reference

Canonical JSON Schema: [`docs/schemas/ctd-mapping-record.schema.json`](../../../docs/schemas/ctd-mapping-record.schema.json)

## ICH M4 modules (common technical document)

| Module | Scope | Notes |
|--------|-------|-------|
| **1** | Regional administrative | **Not harmonized** — use `regional-1` + region-specific section ids (FDA 1.1–1.17, EU 1.0–1.10, etc.) |
| **2** | CTD summaries | 2.1 TOC · 2.2 Intro · 2.3 QOS · 2.4 Nonclinical overview · 2.5 Clinical overview · 2.6 Nonclinical summary · 2.7 Clinical summary |
| **3** | Quality | 3.2.S substance · 3.2.P product · 3.2.A appendices · 3.2.R regional |
| **4** | Nonclinical study reports | By study type (pharmacology, PK, tox, etc.) |
| **5** | Clinical study reports | By study / report |

Use **ICH-common** in `submissionContext.region` only for module 2–5 placement guidance. Module 1 always needs a concrete region.

## eCTD placement (high level)

eCTD adds **granularity**, **lifecycle**, and **regional leaf** conventions on top of CTD section ids:

```text
Evidence / intake record → CTD section (M4) → regional eCTD leaf (if region known) → lifecycle (new/replace/delete)
```

Agents propose **section + optional leaf title** only. Lifecycle operations and publishing are **human/RA-system** tasks.

| Region | Spec reference (confirm current version) |
|--------|------------------------------------------|
| US-FDA | FDA eCTD Technical Conformance Guide |
| EU-EMA | EU eCTD implementation guide / validation criteria |
| UK-MHRA | MHRA eCTD guidance |

Set `submissionContext.ectdSpecification` only when the RA team confirms version — otherwise `null` and `needs-review`.

## Typical MARAS → CTD bridges

| MARAS artifact | Often relevant CTD areas |
|----------------|--------------------------|
| CSV / Part 11 / Annex 11 PBIs | 3.2.P.5 (control of product), 3.2.P.3 (manufacture), regional Module 1 quality attestations |
| Validation IQ/OQ/PQ evidence | 3.2.P.5, 3.2.S.4 (control of critical steps), facility sections in regional Module 1 |
| Clinical GCP / E6 computerised systems | Module 5 study reports, 2.5 clinical overview |
| GMP / data integrity gaps | QOS 2.3 cross-reference; quality Module 3 supporting sections |

These are **placement hints**, not automatic mappings. Every mapping needs `sourceRefs` + `placementRationale`.

## Coverage levels

| `coverageLevel` | Meaning |
|-----------------|---------|
| `supports-section` | Evidence appears to substantively support content for this section |
| `partial` | Evidence touches the topic but gap requires review for full section needs |
| `placeholder-only` | Document listed; substantive content not evidenced |
| `unclear` | Section fit uncertain — RA review required |
| `gap` | Expected section content not evidenced in supplied sources |

## Minimal example

```json
{
  "schemaVersion": "maras.ctd-mapping.v1",
  "recordId": "CTD-2026-08-29-PART11-VAL",
  "status": "needs-review",
  "submissionContext": {
    "region": "US-FDA",
    "productType": "small-molecule",
    "applicationType": "NDA",
    "ectdSpecification": null,
    "submissionUnit": null
  },
  "mappings": [
    {
      "mappingId": "M001",
      "ctdModule": "3",
      "ctdSection": "3.2.P.5",
      "sectionTitle": "Control of Drug Product",
      "ectdLeafTitle": null,
      "placementRationale": "Evidence indicates computerised system audit-trail controls may support manufacturing data integrity statements in control-of-product documentation; gap requires review for full 3.2.P.5 completeness.",
      "sourceRefs": {
        "intakeRecordId": null,
        "evidenceRecordId": "EVR-2026-08-29-PART11-0110e",
        "evidenceClaimId": "C001",
        "marasPbiId": "CFR-001",
        "controlledDocId": null
      },
      "verbatimExcerptRef": "EVR-2026-08-29-PART11-0110e claims.C001.verbatimExcerpt",
      "coverageLevel": "partial",
      "reviewFlags": ["regional-mismatch"],
      "reviewerActionNeeded": "RA confirm whether Part 11 evidence belongs in 3.2.P.5 vs regional Module 1 for this NDA."
    }
  ],
  "unmappedSources": [],
  "coverageNotes": ["Mapping covers audit-trail evidence only; full Module 3 quality tree not assessed."],
  "gaps": ["3.2.P.5 analytical procedures not evidenced in supplied batch."],
  "uncertainties": ["eCTD specification version not confirmed by RA."],
  "reviewerActionNeeded": ["SME/QA/RA review required before any publishing action."],
  "mappedAt": "2026-08-29T17:51:00Z"
}
```

## Validation

```bash
python3 .cursor/skills/ctd-ectd-mapper/scripts/validate_ctd_mapping.py path/to/mapping.json
```

## Upstream skills

- [`regulatory-source-intake`](../regulatory-source-intake/SKILL.md) — DRIVE sources only
- [`regulatory-evidence-extraction`](../regulatory-evidence-extraction/SKILL.md) — verbatim claims required before mapping
