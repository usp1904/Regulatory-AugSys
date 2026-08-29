---
name: controlled-authoring
description: Prepares structured draft authoring packages for controlled documents (SOP, work instruction, policy, specification, validation protocol) with document-control metadata, section outlines, change rationale, and regulatory traceability into JSON conforming to docs/schemas/controlled-authoring-record.schema.json. Use when the user explicitly invokes controlled document authoring, SOP drafting, revision scoping, or document-control package preparation — never auto-invoke.
disable-model-invocation: true
---

# Controlled Authoring

High-risk regulated workflow. **Only run when the user explicitly invokes this skill.**

## Purpose

Prepare a structured **draft** authoring package for a controlled document — without QMS release, approval, or effective-date claims.

## Non-negotiable rules

- Never invent document id, version, approver, effective date, or regulatory citation.
- `documentControl.documentStatus` must remain a draft state (`Draft`, `Draft-For-Review`, `Draft-In-Revision`).
- Always set `controls.packageStatus` to `DRAFT_NOT_CONTROLLED`, `approvedForUse: false`, `effectiveInQms: false`.
- Regulatory traceability requires `verbatimExcerpt` or `evidenceClaimId` — no unsourced requirements.
- Distinguish machine-generated draft prose from customer-approved controlled text; flag `machine-generated` where applicable.
- Never state that a document is approved, effective, released, or under document control in the QMS.
- Use “draft for review,” “proposed wording,” and “SME/QA/RA review required.”
- Agents may set `draft` or `needs-review` only. **`reviewer-approved` is human-only.**

## Graph

```text
Upstream impact/compare/evidence → Document control envelope → Sections → Traceability → Validate → JSON
```

## Workflow

```
Task Progress:
- [ ] 1. Confirm explicit user invocation
- [ ] 2. Define documentType, authoringPurpose, documentControl
- [ ] 3. Draft sections with ordered content
- [ ] 4. Link regulatoryTraceability to sections
- [ ] 5. Document changeRationale, gaps, uncertainties
- [ ] 6. Write JSON; run validate_controlled_authoring.py until exit 0
```

### Step 1 — Confirm invocation

Stop unless the user explicitly asked for controlled document authoring or SOP drafting.

### Step 2 — Document types

| `documentType` | Typical use |
|----------------|-------------|
| `sop` | Standard operating procedure |
| `work-instruction` | Step-level WI |
| `policy` | Quality or IT policy |
| `specification` | URS/FRS/spec |
| `validation-protocol` | IQ/OQ/PQ draft |
| `change-control-record` | Change package narrative |
| `custom` | User-defined — document in `uncertainties` |

| `authoringPurpose` | When |
|--------------------|------|
| `new` | First issue |
| `revision` | Supersedes prior version — set `supersedesVersion` |
| `obsolescence` | Retirement draft |
| `periodic-review` | Scheduled review with optional edits |
| `custom` | User-defined |

### Step 3 — Upstream inputs

Prefer when available:

1. [`regulatory-change-impact`](../regulatory-change-impact/SKILL.md) — revision drivers
2. [`requirements-comparator`](../requirements-comparator/SKILL.md) — SOP vs regulation gaps
3. [`regulatory-evidence-extraction`](../regulatory-evidence-extraction/SKILL.md) — sourced citations

Set `upstreamRefs` when records exist.

### Step 4 — Sections

Minimum sections for `sop` / `work-instruction`:

| Order | Heading (example) |
|-------|-------------------|
| 1 | Purpose |
| 2 | Scope |
| 3 | Responsibilities |
| 4 | Procedure |
| 5 | References |
| 6 | Revision history (proposed) |

Content is **draft prose** — flag `machine-generated` and `needs-sme-wording` as appropriate.

### Step 5 — Regulatory traceability

Each link needs `requirementRef`, neutral `statement`, and `verbatimExcerpt` or `evidenceClaimId`.

Map to authored sections via `linkedSectionIds`.

### Step 6 — Validate

```bash
python3 .cursor/skills/controlled-authoring/scripts/validate_controlled_authoring.py path/to/authoring.json
```

Required envelope:

```json
{
  "schemaVersion": "maras.controlled-authoring.v1",
  "recordId": "AUT-YYYY-MM-DD-DOC",
  "status": "needs-review",
  "documentType": "sop",
  "documentControl": {
    "documentId": "",
    "title": "",
    "proposedVersion": "0.1-draft",
    "documentStatus": "Draft"
  },
  "authoringPurpose": "revision",
  "sections": [],
  "authoredAt": "YYYY-MM-DDTHH:MM:SSZ"
}
```

## Downstream

- [`regulated-document-review`](../regulated-document-review/SKILL.md) — SME worksheet on draft package
- [`regulatory-source-intake`](../regulatory-source-intake/SKILL.md) — register immutable file after customer export (human step)

## MARAS integration

- Customer SOP scenario: combine internal SOP context with FDA/EMA sources; conflicts stay in comparator — do not harmonise in authoring
- PBI `req_id` may appear in `regulatoryTraceability.requirementRef` when traceability is evidenced
- Exports remain `DRAFT_NOT_CONTROLLED` (MVP-10, MVP-12)

## Additional resources

- Field reference: [references/authoring-schema.md](references/authoring-schema.md)
- JSON Schema: [docs/schemas/controlled-authoring-record.schema.json](../../../docs/schemas/controlled-authoring-record.schema.json)
- Safety rules: [`.cursor/rules/regulatory-safety.mdc`](../../../rules/regulatory-safety.mdc)
