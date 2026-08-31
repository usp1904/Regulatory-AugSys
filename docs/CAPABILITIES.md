# Project capabilities (skills, tools, MCP)

Git-only reference for what agents and developers can leverage in **Regulatory-AugSys** without a local install. Canonical branch: **`main`**.

## Quick verification (no local setup)

```bash
node scripts/verify-all.mjs      # full gate
node scripts/self-heal.mjs       # auto-fix ruff + regen workflows, then verify
node scripts/self-heal.mjs --check  # verify only (CI weekly self-heal workflow)
```

Or rely on GitHub Actions on every push to `main`:
- `.github/workflows/ci.yml` — `verify-all`
- `.github/workflows/self-heal.yml` — weekly + manual self-heal check

---

## 1. CRS harness (token optimization)

| Artifact | Purpose |
|----------|---------|
| `Agents.md` | Default agent mode: **Caveman + RTK + Supermemory + Graphiffy** |
| `index.html` → `LIVE_HARNESS_CONFIG` | Browser MVP DeepSeek/GLM token profiles |
| `docs/harness/platform-harness-config.json` | Platform API/web compact context rules |
| `docs/prompts/platform-harness.md` | Cloud Agent instructions for `apps/` |
| `docs/workflows/platform-workflows.json` | Graphify workflow registry + RTK links |

**Graphify pattern:** `Input → Gate → Transform → Evidence → Export (DRAFT_NOT_CONTROLLED)`

---

## 2. Cursor skills (explicit invoke only)

All skills live under `.cursor/skills/`. Each outputs JSON validated against `docs/schemas/*.schema.json`.

| Skill | When to use |
|-------|-------------|
| `regulatory-source-intake` | Register sources, HOLD/DRIVE gates, provenance metadata |
| `regulatory-evidence-extraction` | Atomic source-grounded evidence excerpts |
| `requirements-comparator` | Cross-market / SOP vs regulation comparison |
| `ctd-ectd-mapper` | CTD/eCTD section and leaf placement |
| `regulated-document-review` | SME/QA/RA review worksheets |
| `citation-and-provenance-auditor` | Citation and traceability audit |
| `controlled-authoring` | SOP/WI/policy draft packages |
| `data-integrity-checker` | ALCOA+ assessment |
| `regulatory-change-impact` | Source version change impact |
| `validation-test-generator` | IQ/OQ/PQ draft test packages |

Validators: `.cursor/skills/<name>/scripts/validate_*.py`

---

## 3. Cursor agents & rules

| Path | Purpose |
|------|---------|
| `.cursor/agents/okf-document-pipeline.md` | OKF v0.2 ingestion, chunking, embeddings (platform expansion) |
| `.cursor/rules/regulatory-safety.mdc` | Always-on: no false compliance claims, immutable sources |
| `.cursor/environment.json` | Cloud Agent install: regressions + workflow generation |

---

## 4. MCP servers (Cursor integrations)

| Namespace | Status | Use when |
|-----------|--------|----------|
| **cursor-cloud** | Ready | Run metadata, environment builds, CI diagnostics |
| **cursor-subscriptions** | Ready | Subscribe to GitHub CI/PR events — agents auto-wake on failure to self-heal |
| **Github** | Needs connection | PR/CI inspection (use `gh` CLI as fallback) |
| **Notion** | Needs auth | Import workflows from `docs/workflows/notion-export/` until connected |
| **Figma** | Needs auth | Design assets (not required for current MVP) |

**Notion without MCP:** run `node scripts/generate-notion-workflows.mjs`, then Notion → Import → Markdown on `docs/workflows/notion-export/`.

---

## 5. Platform stack (`apps/`)

| Layer | Tech | Key routes |
|-------|------|------------|
| API | FastAPI, SQLAlchemy, Alembic | `/api/v1/documents`, `/evidence`, `/dossiers/{id}/export`, `/ctd-engine/validate` |
| Web | Next.js, Tailwind | `/`, `/ctd`, `/documents/{id}`, `/evidence/review/{id}`, `/dossiers` |
| Shared services | `ctd_ordering`, `evidence_queries`, `document_storage` | CTD sort, approved evidence lists, immutable files |

---

## 6. Browser MVP (`index.html`)

| Tab | Graph |
|-----|-------|
| Assure | Scope → Intake → Govern → Decompose → QC → Evidence |
| Global Compare | Topic → Market matrix → Diff → Co-op deliverable |
| Readiness | Regulation ↔ SOP map → Gap flags → Inspection pack |
| CTD/eCTD Engine | Documents → Scope → Validate → Gap report |

Verified by: `p0-regression.mjs`, `qc-compat-regression.mjs`

---

## 7. Regression & RTK

| Script | Covers |
|--------|--------|
| `p0-regression.mjs` | MVP UI, harness, skills presence, platform workflows |
| `qc-compat-regression.mjs` | QC layer does not empty corpus or drop fields |
| `apps/api` pytest | API business rules (36+ tests) |
| `apps/web` build | TypeScript, lint, Next.js compile |

MVP requirement IDs: `README.md` RTK table (MVP-01 … MVP-25).

---

## 8. What not to break

- Legacy `index.html` GitHub Pages MVP must keep passing `p0-regression.mjs`
- All exports remain `DRAFT_NOT_CONTROLLED` / training watermark
- Approved-only evidence in dossier exports; pending/rejected never included
- Audit events on document, evidence, and export mutations
