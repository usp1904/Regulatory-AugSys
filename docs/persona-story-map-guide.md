# MARAS Story Map — Persona Lenses (DRAFT_NOT_CONTROLLED)

Six non-overlapping **persona lenses** filter the Story Map workspace so each role sees only its delivery concerns. This does not duplicate Assure, SOP mapper, Global Compare, or Readiness engines—it links to them.

| Lens | Primary panel id | Focus |
|------|------------------|--------|
| System Owner | `story-map-panel-system-owner` | DRAFT posture, release boundaries, risk, approval / IRG links |
| Product Owner | `story-map-panel-product-owner` | Backlog ordering, MoSCoW slices, planned/deferred |
| Product Manager | `story-map-panel-product-manager` | Template, Outcome/OKR view, stakeholder narrative |
| Developer | `story-map-panel-developer` | Modules, dependencies, AC, blocked/planned |
| Tester | `story-map-panel-tester` | Evidence, OQ-style AC, gap/compare/SOP trace |
| Scrum Master | `story-map-panel-scrum-master` | WIP, blockers, PI slices, ceremony JSON export |

**Export:** JSON exports include `personaLens`, `personaLensLabel`, and `personaLensPrimaryPanel`. Scrum Master lens can export `DRAFT-MARAS-Story-Map-Ceremony.json`.

**PBI cards:** Story cards surface **Product Owner understands**, **Developer builds**, and **QA validates** (see `docs/pbi-output-format.md`). Regulatory trace links collapse under **Compliance Details**. CSV/JSON export `pbi.*` fields.

SME/QA/RA review required before baselining; not a compliance decision.
