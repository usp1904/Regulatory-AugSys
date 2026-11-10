# Definition of Done & PO review readiness (DRAFT_NOT_CONTROLLED)

MARAS derives **recommended** Definition of Ready (DoR) / PO review readiness and **recommended** Definition of Done (DoD) checklists from the 19-stage regulatory trace pipeline (`maras.trace-pipeline.v1`). Outputs are draft suggestions only — not approval, not validation, not inspection-ready.

## PO review readiness (Pre-PO review)

Shown on Value Package story cards, Story Map cards, and Pipeline Trace summaries as **Definition of Ready / PO review readiness**.

| Key | Business label | Typical satisfying data |
|-----|----------------|-------------------------|
| `clausesMapped` | Clauses mapped | `regRef`, regulation + section; `REGULATORY_INTENT` node |
| `conditionsIdentified` | Conditions identified | `CONDITIONS` stage without `needs-review` |
| `exceptionsIdentified` | Exceptions identified | `EXCEPTIONS` resolved or `organisationApplicability` |
| `definitionsAnalyzed` | Definitions analyzed | `maras.structured-obligation.v1` or OBLIGATION payload |
| `acceptanceCriteriaGenerated` | Acceptance Criteria generated | `story.ac` / `ACCEPTANCE_CRITERIA` stage |
| `complianceOutcomeIdentified` | Compliance outcome identified | `COMPLIANCE_OUTCOMES` observable |
| `traceabilityComplete` | Traceability complete | `TRACEABILITY_MATRIX`, `traceId`, `regRef` |
| `ambiguitiesReviewed` | Ambiguities reviewed | No `needs-review` on obligation/condition/test stages |
| `productOwnerReviewReady` | Product Owner review ready | All rows above + PBI three questions complete |

Schema: `maras.po-readiness-checklist.v1` on `definitionOfReady.poReadiness`.

Pipeline stage **16 (`DEFINITION_OF_READY`)** carries the full `payload` including this checklist.

## Recommended Definition of Done

Shown as **Recommended Definition of Done (draft)** — MARAS never marks a story “Done” in the product sense.

| Key | Label | Auto-check hint |
|-----|-------|-----------------|
| `acceptanceCriteriaPassed` | Acceptance Criteria passed | Given/When/Then AC + QA validates section |
| `complianceTestsPassed` | Compliance Tests passed | `COMPLIANCE_TEST_SCENARIOS` + RTM test evidence |
| `evidenceCaptured` | Evidence captured | Test/evidence fields populated |
| `auditTrailMaintained` | Audit trail maintained | Chained `traceId` on pipeline nodes |
| `traceabilityRetained` | Traceability retained | Layer 1 verified + Layer 2 approved |
| `exceptionsValidated` | Exceptions validated | EXCEPTIONS / applicability |
| `reportingObligationsSatisfied` | Reporting obligations satisfied | Structured obligations + outcomes |
| `complianceReviewCompleted` | Compliance review completed | SME review attested (draft) |
| `productOwnerApprovalObtained` | Product Owner approval obtained | **Manual** toggle (`localStorage` key `maras.po-approval.v1`) |

Schema: `maras.recommended-dod.v1` on `definitionOfDone.recommendedDoD`.

Pipeline stage **17 (`DEFINITION_OF_DONE`)** carries the aggregate `done` flag (`DRAFT_DONE_CRITERIA_MET` | `NOT_DONE`) plus recommended checklist — still `DRAFT_NOT_CONTROLLED`.

## Exports

`DRAFT-MARAS-Human-Review-Package.json` includes:

- `poReadinessChecklists` — per-PBI PO readiness rows
- `recommendedDefinitionOfDone` — per-PBI recommended DoD rows

## Review

SME/QA/RA review required before baselining. Manual PO approval in MARAS is a local draft toggle only — not a regulated sign-off.
