---
name: validation-test-generator
description: Generates structured draft validation test packages (IQ, OQ, PQ, regression) with requirement traceability, Given/When/Then-style steps, and MARAS PBI linkage into JSON conforming to docs/schemas/validation-test-package-record.schema.json. Use when the user explicitly invokes validation test generation, CSV test protocol drafting, or RTM test coverage scoping — never auto-invoke.
disable-model-invocation: true
---

# Validation Test Generator

High-risk regulated workflow. **Only run when the user explicitly invokes this skill.**

## Purpose

Propose draft validation test cases and traceability for a system under test — without claiming execution, pass results, or qualification.

## Non-negotiable rules

- Never invent requirement ids, regulation citations, test results, or execution timestamps.
- Every test case must link to at least one `requirementRef` (PBI `req_id`, regulation clause, or SOP section).
- Substantive regulatory coverage requires `sourceEvidence.verbatimExcerpt` or `evidenceClaimId`.
- Include negative tests where MARAS inspection readiness expects them (access denial, audit-trail tamper attempts).
- Always set `controls.executed: false`, `controls.passed: false`, `packageStatus: DRAFT_NOT_CONTROLLED`.
- Never state that validation is complete, the system is qualified, or IQ/OQ/PQ passed.
- Use “proposed test,” “draft protocol,” and “SME/QA review required.”
- Agents may set `draft` or `needs-review` only. **`reviewer-approved` is human-only.**

## Graph

```text
Requirements/PBIs/evidence → Test cases → Traceability matrix → Environment notes → Validate → JSON
```

## Workflow

```
Task Progress:
- [ ] 1. Confirm explicit user invocation
- [ ] 2. Define testPhase and systemUnderTest
- [ ] 3. Draft testCases with steps and requirementRefs
- [ ] 4. Build traceability rows; flag gaps
- [ ] 5. Document environmentRequirements and reviewFlags
- [ ] 6. Write JSON; run validate_test_package.py until exit 0
```

### Step 1 — Confirm invocation

Stop unless the user explicitly asked for validation test generation.

### Step 2 — Test phases

| `testPhase` | Use when |
|-------------|----------|
| `iq` | Installation/configuration verification |
| `oq` | Functional and security control testing |
| `pq` | Performance under routine conditions |
| `combined` | Single package spanning multiple phases |
| `regression` | Re-test after change |
| `smoke` | Minimal critical-path checks |
| `custom` | User-defined — document in `uncertainties` |

Record `systemUnderTest.gampCategory` when known (GAMP 1–5).

### Step 3 — Upstream inputs

Prefer:

1. MARAS PBI `req_id`, `source`, and `acceptanceCriteria` (Given/When/Then)
2. [`regulatory-evidence-extraction`](../regulatory-evidence-extraction/SKILL.md) claims
3. [`controlled-authoring`](../controlled-authoring/SKILL.md) SOP procedure sections
4. [`regulatory-change-impact`](../regulatory-change-impact/SKILL.md) for regression scope

### Step 4 — Test case structure

Each case needs:

- `objective` — neutral purpose statement
- `testType` — `positive`, `negative`, or `edge-case`
- `steps[]` — `action` + `expectedObservation` (Given/When/Then aligned)
- `requirementRefs[]` — traceable ids only

Flag `machine-generated`, `environment-not-defined`, or `dual-signoff-required` when applicable.

### Step 5 — Traceability

| `coverageStatus` | Meaning |
|------------------|---------|
| `proposed` | Test draft linked to requirement |
| `gap` | Requirement lacks proposed test |
| `needs-review` | Coverage uncertain |

Mirror MARAS RTM expectations — gaps go in `gaps[]`, not hidden.

### Step 6 — Validate

```bash
python3 .cursor/skills/validation-test-generator/scripts/validate_test_package.py path/to/package.json
```

Required envelope:

```json
{
  "schemaVersion": "maras.validation-test-package.v1",
  "recordId": "VTG-YYYY-MM-DD-SYSTEM",
  "status": "needs-review",
  "testPhase": "oq",
  "systemUnderTest": { "systemId": "", "systemName": "" },
  "testCases": [],
  "generatedAt": "YYYY-MM-DDTHH:MM:SSZ"
}
```

## MARAS integration

- Align steps with PBI Given/When/Then acceptance criteria quality rubric
- Inspection readiness: surface missing negative tests via `gaps` and `reviewFlags`
- IQ/OQ/PQ chunk `c9` / Annex 15 — cite only when evidence record supplied
- Do not claim GAMP 5 licensed full-text mapping without `DRIVE` intake

## Downstream

Packages may feed [`regulated-document-review`](../regulated-document-review/SKILL.md), [`citation-and-provenance-auditor`](../citation-and-provenance-auditor/SKILL.md), and evidence packaging workflows.

## Additional resources

- Field reference: [references/test-package-schema.md](references/test-package-schema.md)
- JSON Schema: [docs/schemas/validation-test-package-record.schema.json](../../../docs/schemas/validation-test-package-record.schema.json)
- Safety rules: [`.cursor/rules/regulatory-safety.mdc`](../../../rules/regulatory-safety.mdc)
