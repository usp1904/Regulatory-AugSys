# Platform agent harness (CRS + DeepSeek token profile)

Use on every Cloud Agent task touching `apps/api` or `apps/web`.

## CRS mode

| Pillar | Rule |
|--------|------|
| **Caveman** | Smallest safe diff; no new abstractions for one-off logic. |
| **RTK** | Map to `MVP-23` / `MVP-24` / `MVP-26` in README; run listed pytest or regression. |
| **Supermemory** | Reuse `ctd_ordering`, `evidence`, `dossier_export`, `document_storage`, `app.agents` — do not fork sort/export/select rules. |
| **Graphify** | State the flow in one line: `Input → Gate → Transform → Evidence → Export`. |

## Token optimization (mirror browser harness)

Config: [`docs/harness/platform-harness-config.json`](../harness/platform-harness-config.json)

- **Compact context**: cap excerpts and summaries at 280 chars in agent prompts.
- **Scoped sources**: cite only ranked/approved records; never paste full document text.
- **Single snapshot**: pass dossier ID + evidence IDs once; avoid repeating manifest fields.
- **DeepSeek profile**: `compact: true`, `omitContextInSystemPrompt: true`, scoped chunks for decomposition-only steps.

Browser MVP equivalent: `LIVE_HARNESS_CONFIG`, `buildHarnessContextLine`, `buildScopedSourceSummary` in `index.html`.

## Workflow registry

Before adding features, check [`docs/workflows/platform-workflows.json`](../workflows/platform-workflows.json).

Regenerate Notion pages after edits:

```bash
node scripts/generate-notion-workflows.mjs
```

## Non-negotiables

- All exports watermarked: `TRAINING / INTERNAL REVIEW ONLY — NOT A REGULATORY SUBMISSION`
- Audit events on create, update, review, export, and agent run (including denied)
- Never claim submission-ready or Part 11 compliance from browser review
- Agent outputs stay `needs-review`; RAG uses derived extracts only
