# Regulatory trace pipeline (MARAS)

**Status:** DRAFT_NOT_CONTROLLED — internal delivery trace model only. Not a compliance decision, validation record, or submission package.

## Purpose

MARAS links curated regulatory sources to delivery artifacts through a **19-stage conversion chain**. Each stage carries `traceId`, `parentTraceId`, and `stage` (enum) so exports and the Value Package RTM remain auditable without replacing SME/QA review.

## Stage enum (`maras.trace-pipeline.v1`)

| # | Stage key | Typical artifact |
|---|-----------|------------------|
| 1 | `DOCUMENT` | Library chunk, ingested source, SHA-256 / excerpt |
| 2 | `REGULATORY_INTENT` | Clause intent from corpus or SME interpretation |
| 3 | `OBLIGATION` | Normative requirement / RAG-synthesized OBL-*; payload may include `maras.structured-obligation.v1` |
| 4 | `CONDITIONS` | Constraints, environmental or procedural conditions |
| 5 | `EXCEPTIONS` | Applicability exceptions (often needs-review) |
| 6 | `BUSINESS_RULES` | ACCEPT action / control statement |
| 7 | `COMPLIANCE_OUTCOMES` | Observable compliance outcomes with `sourceSupport` quotes |
| 8 | `BUSINESS_CAPABILITIES` | Capability impact rows (`new` \| `enhance` \| `retire`) |
| 9 | `VALUE_STREAMS` | Journey / lifecycle touchpoints (inferential fields need review) |
| 10 | `AGILE_GOALS` | PI / programme goal |
| 11 | `EPICS` | Epic name |
| 12 | `FEATURES` | Feature / PBI title |
| 13 | `USER_STORIES` | Business PBI narrative |
| 14 | `ACCEPTANCE_CRITERIA` | Given/When/Then AC |
| 15 | `COMPLIANCE_TEST_SCENARIOS` | Test trace / RTM test column |
| 16 | `DEFINITION_OF_READY` | INVEST + PBI three questions + `maras.po-readiness-checklist.v1` (9 PO review rows) |
| 17 | `DEFINITION_OF_DONE` | RTM Layer 1/2 + `maras.recommended-dod.v1` (9 rows; PO approval manual) |
| 18 | `TRACEABILITY_MATRIX` | Feature Traceability Matrix row |
| 19 | `HUMAN_REVIEW_PACKAGE` | SME checklist bundle (`maras.human-review-package.v1`) |

## Where it appears in the UI

- **Value Package:** collapsed **Delivery Package & traceability** bundle (hard-fail banner, Feature Traceability Matrix, nested **Show pipeline trace**; `maras.final-output-order.v1` sections remain in JSON / Human Review Package exports); per-PBI cards stay three questions + PO readiness + Recommended DoD; **Compliance Details** links to the package bundle (no duplicate per-PBI delivery panels).
- **Story Map:** **Regulatory traceability** view mode shows stage counts and expandable chains.
- **Readiness:** Implementation Readiness Gate references the same 19-stage model in `pipelineNote`.

## Hard-fail and final output order

- `validateRegulatoryOutputHardFail(story, chain, structuredObligations)` returns `{ passed, failures[] }` with stable codes (see [hard-fail-output-governance.md](./hard-fail-output-governance.md)).
- `assembleFinalOutputPackage(story, index)` maps trace pipeline + source fields into 23 sections — stubs are `needs-review`, never invented regulatory text.
- Package-level coverage for section 21 uses pipeline stage completeness (% stages without `needs-review` with summary text).

## Exports

- `DRAFT-MARAS-Backlog.json` — includes `regulatoryTracePipeline` and `traceStageEnum`.
- `DRAFT-MARAS-Human-Review-Package.json` — full chain + `structuredObligations` (`maras.structured-obligation.v1`) + SME review checklist (draft).
- Saved browser packages (`pkg_*`) persist `regulatoryTracePipeline`.
- Story Map JSON includes `assureRegulatoryTracePipeline` when Assure PBIs exist in session.

## AI / harness

Decomposition prompts request `regulatoryTraceHints` on each PBI and verbatim modal language for normalization. See [structured-obligation-normalization.md](./structured-obligation-normalization.md). Missing source material should use `needs-review` stubs — never invent regulatory text.

## Review

Evidence gaps and machine-derived stages require **SME/QA/RA review** before baselining. MARAS does not assert compliance or approval.
