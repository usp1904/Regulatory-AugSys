# MARAS v6.4.1 MVP

MARAS is a stakeholder-review MVP for Pharma and Life Sciences teams. It converts a scoped set of curated regulatory control summaries into a draft assurance package containing regulatory work items, acceptance criteria, risk context, evidence needs, and Jira/ADO/JSON exports.

## Intended stakeholders

- Regulatory Affairs and Compliance: applicability, jurisdiction, and source review.
- Quality Assurance: control, evidence, and approval review.
- Validation/CSA/CSV teams: test obligations and traceability.
- System Owners and Business Analysts: system context and business process fit.
- Product Owners and delivery teams: reviewed backlog export and sequencing.
- Internal Audit: traceability and outstanding clarification review.

## Safe MVP workflow

1. Select the regulated system type, Pharma/Life Sciences domain, jurisdiction, and source scope.
2. Define a measurable business outcome and compliance requirement.
3. Generate a draft package in Demo mode. Use **Quick demo** for the controlled LIMS/Part 11 scenario.
4. Review the captured public-source excerpt, version metadata, and authoritative link; items remain `SME_PENDING` until approval occurs in a controlled system.
5. Enter reviewer name, role, and comment, then record **SME review attested (draft)**, **Clarify**, or **N/A**.
6. Export the watermarked draft. Jira, ADO, FDA-schema, and JSON exports remain `DRAFT_NOT_CONTROLLED` regardless of browser review status.

## Important limitations

- Generated content is a draft, not regulatory or legal advice.
- Public FDA/eCFR demo controls include captured excerpts and source-version metadata. These are still pending SME approval and are not controlled copies.
- Licensed GAMP 5 and ISO content is excluded from generation until a customer-controlled licensed source is available.
- Regulatory and requirement file inputs are disabled because the static MVP has no validated parser, document hashing, malware scan, or source-approval service.
- Saved packages use browser local storage and are not controlled records. Export JSON into the organisation's approved document repository for retention.
- Live AI is an experimental bring-your-own-key browser integration. It sends entered context directly to the selected provider. Do not use confidential, patient-identifiable, personal, or proprietary regulated data.
- Native Jira creation, RBAC, electronic signatures, immutable audit trails, controlled source ingestion, and regulatory change monitoring are phased capabilities and are intentionally not claimed by this MVP.

## Requirement-to-test traceability (RTK)

| ID | MVP requirement | Verification |
|---|---|---|
| MVP-01 | Block generation without system, domain, jurisdiction, outcome, sources, and requirement | Blank-submit browser test displays an accessible error summary |
| MVP-02 | Keep the Pharma LIMS sample in relevant control categories | Quick demo produces applicable public-source controls; medical-device-only and licensed sources are excluded |
| MVP-03 | Do not present automated scoring as regulatory approval | Output is labelled Draft; missing SME source approval forces Grade REVIEW and zero automated passes |
| MVP-04 | Provide authoritative-source navigation | Every Quick-demo PBI contains an official/public or publisher source link |
| MVP-05 | Produce readable business requirements | Regression test rejects known `must attributable`/noun-phrase grammar defects |
| MVP-06 | Preserve accountable draft review decisions | Each PBI records reviewer name, role, comment, timestamp and append-only-in-session history; exports include the fields |
| MVP-07 | Prevent rendered input/model content from executing HTML | Browser injection regression confirms escaped text and no script/image execution |
| MVP-08 | Warn before external AI transmission | Live AI requires an explicit provider/data warning confirmation |
| MVP-09 | Prevent false file-ingestion claims | Both upload controls are disabled and labelled as production gates |
| MVP-10 | Keep readiness internally consistent | Missing evidence yields `NOT_READY`, score 0, draft document states, and `submission_ready: false` |
| MVP-11 | Keep source mappings precise | FDA CSA is identified as nonbinding, medical-device guidance; GAMP 5 and ISO remain license-gated |
| MVP-12 | Prevent uncontrolled exports from appearing approved | All exports and saved packages are permanently marked `DRAFT_NOT_CONTROLLED` |
| MVP-13 | Validate every supported regulated system | Regression matrix covers LIMS, MES, SCADA/DCS, Serialization, QMS, EDMS, CDS, PV, EDC/eCRF, CTMS, eTMF, Safety Reporting, RIM, ERP/SAP, and Supply Chain |
| MVP-14 | Keep Saved Package controls usable at the larger type size | Label, inputs, Save button, status and note increase by 2px; flex wrapping and shrink-safe inputs keep every control inside the bordered container |
| MVP-15 | Align first-time guidance with the assurance workflow | Versioned guide is re-enabled once for existing users, sits directly above the assurance hero, shares its content boundaries, and the Regulatory Library uses a wider responsive panel |

## Stakeholder demo script

1. Open `index.html` and click **Quick demo**.
2. Show the automatically scoped FDA/LIMS/Pharma context.
3. Generate the draft and review the readiness banner.
4. Open a source link from a PBI.
5. Enter reviewer identity and a comment, expand acceptance criteria, and record a draft review attestation.
6. Export Jira CSV or JSON and show the `DRAFT_NOT_CONTROLLED` watermark.

## Deployment

The deliverable remains a static single-file application. Replace the existing GitHub Pages `index.html` with the MVP file, review it in a non-production branch, and publish only after the source owner confirms the official links and permitted-use statements.
