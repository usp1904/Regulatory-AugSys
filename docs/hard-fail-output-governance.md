# Hard-fail output governance (MARAS)

**Status:** DRAFT_NOT_CONTROLLED — automated rejection heuristics only. Not a compliance decision, validation record, or submission package.

## Policy

- **OUTPUT ONLY SOURCE SUPPORTED** — delivery sections populate from `maras.trace-pipeline.v1`, ingested excerpts, and existing story fields only.
- **DRAFT_NOT_CONTROLLED** — all exports retain draft watermarks; SME/QA/RA review is still required when hard-fail passes.
- **ZERO_UNSUPPORTED_STATEMENTS** — `validateRegulatoryOutputHardFail` separates **blocking** failures (missing source/trace, invented technology/architecture/vendor/design) from **review warnings** (minor unsupported narrative, conditions/exceptions needs-review when trace is otherwise anchored). PBI fields derived via `MARAS_ALLOWED_DERIVATION_PREFIXES` (e.g. `Priority:`, `Given`, `Evidence stage:`) are not treated as unsupported claims.

## Hard-fail codes

| Code | Trigger (summary) |
|------|-------------------|
| `SOURCE_MISSING` | No excerpt, regRef, regulation, or library chunk |
| `CLAUSE_MISSING` | Section / clause identifier absent |
| `TRACEABILITY_MISSING` | traceId, regRef, or pipeline chain incomplete |
| `OBLIGATION_MISSING` | Modal shall/must/required language in corpus but no structured obligations |
| `CONDITION_OMITTED` | Conditional language in source; CONDITIONS stage needs-review |
| `EXCEPTION_OMITTED` | Exception language in source; EXCEPTIONS unresolved |
| `THRESHOLD_OMITTED` | Threshold language in source not reflected in compliance outcomes |
| `DEFINITION_OMITTED` | Definition language in source; definitions not captured |
| `TABLE_IGNORED` | Table markers in excerpt context |
| `REFERENCE_IGNORED` | Cross-reference in source not mapped |
| `UNSUPPORTED_STATEMENT` | Specific compliance/approval or numeric claim without SME-approved citation — **warning** when source, clause, and trace anchor present |
| `TECHNOLOGY_INVENTED` | Technology term absent from source corpus |
| `ARCHITECTURE_INVENTED` | Architecture pattern absent from source corpus |
| `VENDOR_INVENTED` | Vendor/product absent from source corpus |
| `DESIGN_INVENTED` | Design artifact absent from source corpus |

Package-level UI shows one banner (max **5** unique codes, `+N more`). Per-PBI cards do not repeat the full banner. **Blocking** codes set `regulatoryOutputHardFail.passed` to **false** and exports use a **FAILED** package status prefix. **WARN_NEEDS_REVIEW** codes alone keep `passed` true with DRAFT_NOT_CONTROLLED watermark. Empty stub sections remain `needs-review`, not invented filler.

## Final output order (`maras.final-output-order.v1`)

Twenty-three numbered sections per PBI, assembled by `assembleFinalOutputPackage(story, index)`:

1. Regulatory Intent Summary  
2. Regulatory Knowledge Graph  
3. Definitions  
4. Obligations  
5. Conditions  
6. Exceptions  
7. Prohibitions (from structured obligation modality `PROHIBITED`)  
8. Compliance Outcomes  
9. Business Capabilities  
10. Value Stream Impacts  
11. Agile Goals  
12. Epics  
13. Features  
14. User Stories  
15. Acceptance Criteria  
16. Compliance Test Cases  
17. Evidence Requirements  
18. Definition of Ready  
19. Definition of Done  
20. Traceability Matrix  
21. Coverage Report (RTM coverage % from pipeline completeness)  
22. Validation Rubric  
23. Human Review Checklist  

The **Delivery Package** panel on the Value Package tab surfaces persona essentials (PO, Dev, Tester, PM, System Owner, RTE/PM) and expandable sections 1–23 per PBI. PBI three questions remain the default visible narrative.

## Exports

- `DRAFT-MARAS-Backlog.json` — includes `regulatoryOutputHardFail`, `finalOutputPackages`, and `finalOutputOrderSchema`.
- When hard-fail fails: download name `FAILED-DRAFT-MARAS-Backlog.json` and `packageStatus` prefix `FAILED · DRAFT_NOT_CONTROLLED`.
- `DRAFT-MARAS-Human-Review-Package.json` — same hard-fail payload and final output bundles.
- Saved browser packages (`pkg_*`) persist hard-fail and final output metadata.

## Review

Evidence gaps and hard-fail codes require **SME/QA/RA review** before baselining. MARAS does not assert compliance or approval.
