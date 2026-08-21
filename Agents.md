# MARAS Agent Defaults

All Cursor agents, cloud agents, and subagents working on **Regulatory-AugSys** must treat the following as **default instructions** on every task — not optional overrides.

## 1. CRS Mode (always)

Run in **CRS Mode: Caveman + RTK + Supermemory**.

| Pillar | Requirement |
|--------|-------------|
| **Caveman** | Plain-language outcomes first; minimal scope; no over-engineering; smallest safe diff that solves the real problem. |
| **RTK** | Every behaviour change maps to an MVP requirement ID in `README.md` with a verification step (`p0-regression.mjs`, `qc-compat-regression.mjs`, or documented manual check). |
| **Supermemory** | Reuse existing corpus (`GXP_CHUNKS`, ingestion gates, harness state `H`, QC layer) instead of duplicating logic; persist cross-tab state when adding features. |

## 2. Graphiffy (always)

**Leverage Graphiffy** — express pipelines as short graph flows in UI copy, assurance notes, and agent summaries.

Preferred pattern:

```text
Input → Gate / QC → Transform → Evidence → Export (DRAFT_NOT_CONTROLLED)
```

Examples in this repo:

- Ingestion: `File → Hash → Parse → Gate → Hold | Drive`
- Assure: `Source → Scope → PBI → Rubric → Evidence package`
- Global Compare: `Topic → Market matrix → Diff → Co-op deliverable`
- Readiness: `Regulation ↔ SOP map → Gap flags → Inspection pack → Download`

Use graphs for visibility, not as a substitute for coded gates or SME approval.

## Repository conventions

- Canonical branch: **`main`** at https://github.com/usp1904/Regulatory-AugSys
- Single-file app: `index.html` (GitHub Pages root)
- Do not claim regulatory approval, electronic signatures, or controlled records from browser-only review
- All exports remain `DRAFT_NOT_CONTROLLED` until customer-controlled systems approve

## Subagents

- Document ingestion post-processing: `.cursor/agents/okf-document-pipeline.md` (OKF v0.2, when ingestion expands beyond browser parse)
