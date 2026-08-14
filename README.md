# MARAS v6.4.0 MVP

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
4. Open every authoritative-source link and verify the exact clause against the controlled source.
5. Mark every item **SME reviewed**, **Clarify**, or **N/A**.
6. Export only after the review decisions are complete. Exports carry source URL, source-assurance status, review status, and automated readiness score.

## Important limitations

- Generated content is a draft, not regulatory or legal advice.
- The embedded corpus contains curated summaries, not verified source excerpts. This is therefore a human-review gate, not a validated source-ingestion system.
- Saved packages use browser local storage and are not controlled records. Export JSON into the organisation's approved document repository for retention.
- Live AI is an experimental bring-your-own-key browser integration. It sends entered context directly to the selected provider. Do not use confidential, patient-identifiable, personal, or proprietary regulated data.
- Native Jira creation, RBAC, electronic signatures, immutable audit trails, controlled source ingestion, and regulatory change monitoring are phased capabilities and are intentionally not claimed by this MVP.

## Requirement-to-test traceability (RTK)

| ID | MVP requirement | Verification |
|---|---|---|
| MVP-01 | Block generation without system, domain, jurisdiction, outcome, sources, and requirement | Blank-submit browser test displays an accessible error summary |
| MVP-02 | Keep the Pharma LIMS sample in relevant control categories | Quick demo produces Part 11, ALCOA+, GAMP/CSA controls and no ISO 13485 device controls |
| MVP-03 | Do not present automated scoring as regulatory approval | Output is labelled Draft; unverified excerpts force Grade REVIEW and zero automated passes |
| MVP-04 | Provide authoritative-source navigation | Every Quick-demo PBI contains an official/public or publisher source link |
| MVP-05 | Produce readable business requirements | Regression test rejects known `must attributable`/noun-phrase grammar defects |
| MVP-06 | Preserve human review decisions | Each PBI supports SME reviewed, clarification required, or N/A status; exports include the status |
| MVP-07 | Prevent rendered input/model content from executing HTML | Browser injection regression confirms escaped text and no script/image execution |
| MVP-08 | Warn before external AI transmission | Live AI requires an explicit provider/data warning confirmation |

## Stakeholder demo script

1. Open `index.html` and click **Quick demo**.
2. Show the automatically scoped FDA/LIMS/Pharma context.
3. Generate the draft and review the readiness banner.
4. Open a source link from a PBI.
5. Expand acceptance criteria and record a review decision.
6. Export Jira CSV or JSON and explain that Jira is the execution destination while the assurance package is the governed product.

## Deployment

The deliverable remains a static single-file application. Replace the existing GitHub Pages `index.html` with the MVP file, review it in a non-production branch, and publish only after the source owner confirms the official links and permitted-use statements.
