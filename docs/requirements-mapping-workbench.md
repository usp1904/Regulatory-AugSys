# MARAS Requirements Mapping Workbench — Step 1–3

## Purpose

The workbench adds a controlled draft workflow between a regulatory source excerpt and a draft product backlog item. It is intentionally a separate module so the existing single-page app remains intact.

## Traceability chain

`source ID + revision + clause → excerpt → atomic obligation → applicability → system finding/evidence → confirmed interpretation → business requirement → draft PBI → acceptance criteria → verification evidence → reviewer decision`

Each mapping receives a generated `mappingId` and is exported in JSON under schema `maras.requirements-mapping.export.v1`.

## Release checks

The current deterministic validator blocks the `READY_FOR_CONTROLLED_REVIEW` status unless it finds:
- Source ID and revision, authority, HTTPS URL, and source review status set to `APPROVED_FOR_REVIEW`.
- A clause reference, excerpt, and atomic obligation.
- An applicability decision, including rationale when not applicable.
- A system finding and evidence reference, or an explicit reason why system evidence is unknown.
- A confirmed interpretation, accountable decision owner, and no open dependency.
- An observable business requirement, PBI title, acceptance criteria, and verification evidence.
- A named approver and approval decision set to `APPROVED`.

This is a **completeness gate**, not an independent verification of source authenticity, legal interpretation, applicability, or compliance. Source status and reviewer approval are currently user-entered attestations and can be misused. Do not treat this as a validated electronic signature or regulated audit record.

## Clarification lifecycle

- `OPEN`: clarification is unresolved; mapping remains blocked.
- `PROPOSED`: interpretation proposed but not confirmed; mapping remains blocked.
- `CONFIRMED`: accountable decision owner confirms the interpretation.
- `REJECTED`: interpretation rejected; mapping remains blocked.

If a question exists, record a question owner. An `OPEN` dependency blocks readiness; use `RESOLVED` only after recording the evidence that demonstrates resolution in the dependency field/comment.

## Test checklist

Use synthetic/public material only. Never enter patient-identifiable or confidential client data into this browser-only prototype.

1. **Happy path:** valid source metadata, clause excerpt, applicability, verified system evidence, confirmed decision, complete PBI/test details, named approver, and approved status. Expected: completeness gate passes.
2. **Unreviewed source:** set source status to Pending. Expected: blocked.
3. **Unknown system evidence:** choose Unknown and describe missing evidence. Expected: unknown is visible and traceable; no claim that the system is compliant.
4. **Unresolved interpretation:** set decision status to Open or Proposed. Expected: blocked.
5. **Open dependency:** set dependency status to Open. Expected: blocked.
6. **Not applicable without rationale:** expected: blocked.
7. **Missing acceptance criteria or test evidence:** expected: blocked.
8. **Unapproved review:** pending, changes required, or rejected. Expected: blocked.
9. **Unsafe display text:** use a filename or title containing HTML-like text. Expected: displayed as text, never executed.
10. **Export/re-import review:** export JSON and inspect source, decision, system evidence, PBI, approval, and validation fields. Note: import and persistent storage are not implemented yet.

## Known limitations

- Data is held in page memory and is lost on refresh unless exported.
- No server-side database, identity, role-based permissions, immutable audit history, or e-signature.
- The HTTPS URL and approval status are not independently checked by the browser workbench.
- No automatic PDF/DOCX/XLSX parsing or controlled source acquisition.
- No AI extraction/generation in this workbench; it captures and gates a human-reviewed mapping.
- No direct Azure DevOps integration; use export only as a draft artifact.
- No regulatory claim should be made from the numeric/completeness outcome alone.

## Next implementation sequence

1. Validate this data model with a regulatory SME using a public example clause.
2. Add persistent storage, user identity/roles, server-side audit events, and authorization.
3. Implement controlled ingestion with file hashing, parsing, source versioning, malware scanning, and approval workflow.
4. Add evidence-backed obligation extraction and system-impact mapping with explicit unknowns.
5. Add PBI generation plus positive, negative, boundary, and failure acceptance criteria.
6. Add a readiness gate and benchmark suite against SME-approved reference cases.
7. Add authenticated Azure DevOps publishing with stable IDs, idempotent updates, and read-back verification.
