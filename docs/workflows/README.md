# Platform workflow registry

Machine-readable workflows for the MARAS browser MVP (`index.html`) and the Regulatory-AugSys platform (`apps/`). Designed for **CRS Mode** (Caveman + RTK + Supermemory + Graphify) and **DeepSeek harness** token efficiency.

## Source of truth

| Artifact | Purpose |
|----------|---------|
| [`platform-workflows.json`](./platform-workflows.json) | Workflow IDs, Graphify graphs, API routes, verification |
| [`../harness/platform-harness-config.json`](../harness/platform-harness-config.json) | Token + CRS profile for platform agents |
| [`../../Agents.md`](../../Agents.md) | Default agent instructions (CRS + Graphiffy) |
| [`../../index.html`](../../index.html) | `LIVE_HARNESS_CONFIG`, `buildHarnessContextLine` |

## Graphify patterns

```text
Assure:     Scope → Intake → Govern → Decompose → QC → Evidence → Export
Ingestion:  Upload → Hash → Parse → Store → Audit
Evidence:   Capture → Pending → Review → Approved
Dossier:    Approved → CTD order → Render → Manifest → Immutable file
CTD:        Documents → Scope → Validate → Gap report
```

## Notion sync (no local install required)

Workflow pages for Notion are generated in-repo and committed to `main`:

```bash
node scripts/generate-notion-workflows.mjs
```

Import into Notion:

1. Open your Notion workspace → **Import** → **Markdown**.
2. Select files under `docs/workflows/notion-export/`.
3. Map properties: **Workflow ID**, **Graph**, **MVP IDs**, **Verification**.

When the Notion MCP integration is authenticated in Cursor, agents can push updates from `platform-workflows.json` directly.

## Verification (git-only)

```bash
node p0-regression.mjs
node qc-compat-regression.mjs
cd apps/api && pytest && ruff check .
cd apps/web && npm run build
```

All workflows list their verification commands in `platform-workflows.json`.
