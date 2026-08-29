# Validation test package reference

Canonical JSON Schema: [`docs/schemas/validation-test-package-record.schema.json`](../../../docs/schemas/validation-test-package-record.schema.json)

## Test phases

| `testPhase` | Typical scope |
|-------------|---------------|
| `iq` | Hardware, OS, DB install, config baseline |
| `oq` | Functional, security, audit trail, access control |
| `pq` | Routine-load performance, sustained operation |
| `combined` | IQ+OQ or full CSV package draft |
| `regression` | Post-change re-test subset |
| `smoke` | Critical-path only |

## Test types

| `testType` | When |
|------------|------|
| `positive` | Expected-path behavior |
| `negative` | Denied access, invalid input, tamper attempt |
| `edge-case` | Boundary or timing conditions |

MARAS inspection readiness flags missing **negative** coverage for P0 controls.

## Review flags

| Flag | When |
|------|------|
| `machine-generated` | Agent-drafted steps |
| `needs-sme-review` | Technical accuracy unverified |
| `missing-negative-coverage` | Only positive path for security control |
| `environment-not-defined` | Test env not documented |
| `dual-signoff-required` | Execution needs independent reviewer |
| `regulatory-citation-required` | Requirement ref without sourced excerpt |

## Traceability

| `coverageStatus` | Meaning |
|------------------|---------|
| `proposed` | Draft test linked |
| `gap` | No test proposed |
| `needs-review` | Linkage uncertain |

**Never** map `proposed` to “validated” or “qualified.”

## Controls (required)

```json
"controls": {
  "packageStatus": "DRAFT_NOT_CONTROLLED",
  "executed": false,
  "passed": false
}
```

## Minimal OQ example (audit trail)

```json
{
  "schemaVersion": "maras.validation-test-package.v1",
  "recordId": "VTG-2026-08-29-LIMS-AUDIT-OQ",
  "status": "needs-review",
  "testPhase": "oq",
  "systemUnderTest": {
    "systemId": "LIMS-PROD-001",
    "systemName": "GxP Laboratory LIMS",
    "gampCategory": "4",
    "environmentNotes": "Validated test environment — configuration not verified in this batch."
  },
  "testCases": [
    {
      "testId": "TC-OQ-001",
      "title": "Audit trail records operator entry",
      "objective": "Verify audit trail captures operator identity and timestamp for GxP-critical record change.",
      "testType": "positive",
      "preconditions": ["Test user with analyst role exists", "Audit trail enabled for sample record type"],
      "steps": [
        {
          "stepNumber": 1,
          "action": "Given a GxP-critical sample result, when analyst modifies the result, then save the record.",
          "expectedObservation": "Audit trail entry shows user id, timestamp, old value, and new value."
        }
      ],
      "requirementRefs": ["21 CFR Part 11 §11.10(e)", "STORY-AUDIT-TRAIL-001"],
      "sourceEvidence": {
        "citation": "§11.10(e)",
        "verbatimExcerpt": "Use of secure, computer-generated, time-stamped audit trails to independently record the date and time of operator entries and actions.",
        "evidenceClaimId": "C001",
        "marasPbiId": "STORY-AUDIT-TRAIL-001"
      },
      "reviewFlags": ["machine-generated", "environment-not-defined"]
    }
  ],
  "controls": {
    "packageStatus": "DRAFT_NOT_CONTROLLED",
    "executed": false,
    "passed": false
  },
  "generatedAt": "2026-08-29T18:09:00Z"
}
```
