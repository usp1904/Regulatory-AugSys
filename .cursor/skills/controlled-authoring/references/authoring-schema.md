# Controlled authoring reference

Canonical JSON Schema: [`docs/schemas/controlled-authoring-record.schema.json`](../../../docs/schemas/controlled-authoring-record.schema.json)

## Document types

| `documentType` | Typical MARAS context |
|----------------|----------------------|
| `sop` | Customer SOP vs regulation alignment |
| `work-instruction` | Procedure steps under an SOP |
| `policy` | Quality, IT, or data-governance policy |
| `specification` | URS/FRS for validated systems |
| `validation-protocol` | IQ/OQ/PQ narrative draft |
| `change-control-record` | Change package tied to `regulatory-change-impact` |
| `custom` | User-defined |

## Draft document status (agents only)

| `documentStatus` | Meaning |
|------------------|---------|
| `Draft` | Initial agent-prepared draft |
| `Draft-For-Review` | Ready for SME worksheet |
| `Draft-In-Revision` | Revision in progress |

Agents **must not** use `Effective`, `Approved`, or `Released`.

## Section review flags

| Flag | When |
|------|------|
| `machine-generated` | LLM or agent drafted the prose |
| `needs-sme-wording` | Technical accuracy unverified |
| `regulatory-citation-required` | Claim lacks sourced excerpt |
| `scope-unclear` | Applicability boundaries undefined |
| `translation-needed` | Non-authoritative language version |

## Regulatory traceability

Each `traceLink` requires:

- `requirementRef` — regulation clause, PBI `req_id`, or comparator item
- `statement` — neutral traceability note
- `verbatimExcerpt` **or** `evidenceClaimId`
- Optional `linkedSectionIds` tying to authored sections

**Never** state traceability proves compliance.

## Controls (required for agent output)

```json
"controls": {
  "packageStatus": "DRAFT_NOT_CONTROLLED",
  "approvedForUse": false,
  "effectiveInQms": false
}
```

## Minimal SOP revision example

```json
{
  "schemaVersion": "maras.controlled-authoring.v1",
  "recordId": "AUT-2026-08-29-SOP-AUDIT-REVIEW",
  "status": "needs-review",
  "documentType": "sop",
  "documentControl": {
    "documentId": "SOP-CSV-AUDIT-REVIEW-004",
    "title": "Computerised System Audit Trail Review",
    "proposedVersion": "2.1-draft",
    "supersedesVersion": "2.0",
    "documentStatus": "Draft-For-Review",
    "owningDepartment": "Quality Assurance",
    "proposedEffectiveDate": null,
    "language": "en"
  },
  "authoringPurpose": "revision",
  "changeRationale": "Proposed revision to reflect potential Annex 11 audit-trail review expectations identified in change-impact assessment.",
  "sections": [
    {
      "sectionId": "S01",
      "heading": "Purpose",
      "order": 1,
      "purpose": "State why the SOP exists",
      "content": "This draft SOP defines the process for periodic review of computerised system audit trails in GxP environments.",
      "reviewFlags": ["machine-generated", "needs-sme-wording"]
    }
  ],
  "regulatoryTraceability": [
    {
      "linkId": "T001",
      "requirementRef": "EU GMP Annex 11 Cl.10",
      "statement": "Procedure section should address traceability of GxP-critical changes to individuals.",
      "citation": "Annex 11 Cl.10",
      "verbatimExcerpt": "Relevant changes to GxP critical data should be recorded and traceable to the person who made the change.",
      "evidenceClaimId": null,
      "marasChunkId": "c4",
      "linkedSectionIds": ["S04"]
    }
  ],
  "controls": {
    "packageStatus": "DRAFT_NOT_CONTROLLED",
    "approvedForUse": false,
    "effectiveInQms": false
  },
  "authoredAt": "2026-08-29T18:05:00Z"
}
```
