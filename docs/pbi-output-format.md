# MARAS PBI output format (DRAFT_NOT_CONTROLLED)

Generated Assure items and Story Map cards default to a **Product Backlog Item (PBI)** layout that answers three delivery questions in business language:

| Section | Audience | Content |
|---------|----------|---------|
| **Product Owner understands** | PO | Business value, slice, priority hints, acceptance from a business lens |
| **Developer builds** | Dev | Screens, services, APIs, data, behaviors — concrete build bullets |
| **QA validates** | QA | Test themes, pass/fail checks, negative paths |

Regulatory traceability (source refs, REQ ids, interpretation, evidence packages, RTM) stays in the UI under **Compliance Details** (`<details>` collapsed by default).

**Definition of Ready / PO review readiness** and **Recommended Definition of Done (draft)** appear on the default PBI card (business-friendly checklists). Derivation hints (which pipeline stage satisfies each row) sit under Compliance Details. See [definition-of-done.md](./definition-of-done.md).

## Completeness

Each item exposes `pbi.complete` (boolean). It is `true` only when all three sections have substantive text. Otherwise the UI shows **⚠ Incomplete requirement** and lists missing sections.

## JSON shape (Assure export & Story Map)

```json
{
  "pbi": {
    "poUnderstands": "…",
    "devBuilds": "…",
    "qaValidates": "…",
    "complete": false
  }
}
```

Story Map CSV export columns: `pbi.poUnderstands`, `pbi.devBuilds`, `pbi.qaValidates`, `pbi.complete`.

## Persona lenses

- **Product Owner**: editable PBI text areas on story cards (`pbi-editable`).
- **Developer / Tester**: read-only PBI block derived from story fields.

SME/QA/RA review required before baselining; not a compliance or approval decision.
