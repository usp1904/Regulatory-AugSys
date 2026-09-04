# MARAS RAG Graph Optimization Plan (Phase 0 Discovery)

**Repository:** Regulatory-AugSys / MARAS v6.4.1 MVP  
**Scope:** `index.html` single-file application (GitHub Pages root)  
**Status:** Discovery only — no application code modified  
**Date:** 2026-09-04  

---

## Executive summary

MARAS today implements a **4-process assurance pipeline** (Source & Scope Validation → Business Translation → Self-Evaluation → Evidence Package) with an embedded **QC layer** (scope, relevance ranking, jurisdiction filter, dedupe, normalization, rubric scoring). Retrieval is **keyword/Jaccard-based over `GXP_CHUNKS`**, not vector RAG. Live AI uses a **CRS token harness** (`LIVE_HARNESS_CONFIG`) to limit context.

The proposed **RAG Graph** (`Parse → Retrieve → ReRank → Synthesize → Verify → Replay`) maps cleanly onto existing functions with **additive, modular extraction** — not a rewrite. A separate **`apps/web` + `apps/api`** platform exists for CTD/evidence/story-map; it does **not** drive the PBI generator and must remain out of scope until explicitly bridged.

**Recommended next phase:** **Phase 1** — extract RAG stage interfaces as pure functions behind a feature flag, wire `Parse` + `Retrieve` only, with regression fixtures unchanged.

**Phase 1 update (2026-09-04):** Hybrid retrieval (OKF v0.2 adapter + Graph RAG + TF-IDF pseudo-vector) is implemented with **Deterministic First** routing. See [hybrid-retrieval-architecture.md](./hybrid-retrieval-architecture.md).

---

## 1. Current state discovery

### 1.1 Requirement input flow

| Step | Function / element | Lines (approx.) | Behavior |
|------|-------------------|-----------------|----------|
| Project context | `#f-org`, `#f-site`, `#f-proj`, `#f-system`, `#f-outcome`, `#f-client-region`, `#f-client-delta`, `#f-gap-input` | HTML ~680–760 | Captured once in `doGenerate()` ctx snapshot |
| Framework / jurisdiction | `getSelectedFrameworks()`, `getSelectedJurisdictions()`, `applyFramework()`, `applySelectedFrameworks()` | 1666–1950 | Multi-select dropdowns; `FW_LIBRARY_MAP` presets library tree |
| Domain | `buildChips('ch-domain', DOMAINS)`, `selDomain` | 1905–1925 | Required chip selection |
| Regulatory library | `TREE_DATA` tree, `selItems`, `toggleItem()`, `selAll()` | 1075–1175, 1836–1876 | Checkbox tree; `validateMvpInputs()` requires `selItems.size > 0` |
| Control categories | `CATS`, `selCatsSet`, `buildCats()`, `toggleCat()` | 1194–1203, 1885–1905 | Optional scope filter (A–H) |
| Requirement text | `#req-ta`, `REQ_EXAMPLES`, `applyReqExample()`, `buildReqExamples()` | 1176–1193, 1598–1634 | Free text + preset chips/datalist |
| Requirement file upload | `handleReqFiles()`, `parseRequirementPayload()`, `evaluateRequirementIngestionGate()` | 2124–2156, 2879–2910 | TXT/CSV/JSON only; gate HOLD/DRIVE |
| MVP validation gate | `validateMvpInputs()`, `showMvpValidation()` | 1637–1658 | Blocks `doGenerate()` if scope incomplete |
| Demo sample | `loadProductGradeSample()` | 5133–5158 | Seeds LIMS/Part 11 product-grade scenario |
| Orchestrator entry | `doGenerate()` → `orchestratorDemo()` \| `orchestratorLive()` | 3591–3649 | `demoMode` toggle selects path |

**Flow diagram (current):**

```text
User inputs (context + req + library scope)
  → validateMvpInputs()
  → doGenerate() snapshots ctx into H.ctx
  → demoMode ? orchestratorDemo : orchestratorLive
  → rankChunks(req) + applyQualityControls()
  → renderStories()
```

### 1.2 Regulatory library / data structure

All corpus data is **embedded in `index.html`** — no external graph JSON files.

| Structure | Lines | Contents |
|-----------|-------|----------|
| `TREE_DATA` | ~1075–1175 | Sidebar library groups → items (`id`, `name`, `cat`, `n`) |
| `GXP_CHUNKS` | 1267–1289 | Curated regulatory chunks: `id`, `cat`, `reg`, `sec`, `title`, `reqs[]`, `excerpts[]`, `kws[]`, optional `sourceKey`, `licenseGate`, `medicalDeviceOnly` |
| `CONTROLLED_SOURCES` | 1291–1297 | Authority metadata for PART11, FDA_DI, FDA_CSA, GAMP5, ISO13485 |
| `SOURCE_TRUST` | 1299–1332 | Assurance tab source-trust cards |
| `FW_LIBRARY_MAP` | 1215–1231 | Framework → library item id presets |
| `JURISDICTION_BY_FRAMEWORK` | 2333–2349 | Framework → allowed nations |
| `SYSTEM_AFFINITY` | 2351–2373 | System type → keyword affinity for ranking |
| `FDA_CLINICAL_DATA_SCHEMA` | 2375–2393 | Target export schema (`maras.fda.clinical-regulatory-assurance.v1`) |
| Ingested sources | `sbDocs[]`, `INGESTED_SOURCE_META`, `ingestedGenerationChunks()` | 2183–2256, 2949–2952 | User-uploaded sources that pass production gate |

**Chunk shape (canonical):**

```javascript
{
  id, cat, reg, sec, title,
  reqs: string[],      // obligation bullets
  excerpts?: string[], // source text (when captured)
  kws?: string[],
  sourceKey?: string,
  licenseGate?: boolean,
  medicalDeviceOnly?: boolean,
  ingested?: boolean   // runtime flag on ingested chunks
}
```

### 1.3 Source selection and ranking logic

| Function | Lines | Role |
|----------|-------|------|
| `resolveScopeControls()` | 2451–2512 | Builds scope: frameworks, system, jurisdictions, active/tree categories, `allowedNations`, caps |
| `scoreSourceRelevance(chunk, req, scope)` | 2514–2562 | Keyword hits (+4), reg/section/title match, Jaccard on reqs, category boost, system affinity, jurisdiction penalty, domain mismatch (-30) |
| `rankChunks(req)` | 2955–2976 | Filter `GXP_CHUNKS` + `ingestedGenerationChunks()`, score, sort desc, jurisdiction filter, relevance floor |
| `applyJurisdictionFilter(ranked, scope)` | 2564–2579 | Hard-drop OOJ only when alternatives exist; never empty corpus |
| `sourceMetaFor(reg, sourceKey)` | 5160–5183 | Authority, nation, URL, license, approval status |

**Config:** `QC_CONFIG` (2323–2331): `maxScopedChunks: 8`, `maxOutputItems: 24`, `duplicateJaccard: 0.72`, `rubricPassThreshold: 70`.

**Gap vs future RERANK:** No `primary` / `supporting` / `contextual` / `suppressed` / `not_applicable` labels. Jurisdiction suppression is tracked in `_jurisdictionSuppressed` metadata only.

### 1.4 PBI generation logic

| Path | Entry | Lines | Mechanism |
|------|-------|-------|-----------|
| Demo (default) | `runDemoEngine(req, ctx)` | 3275–3518 | Deterministic: top N ranked chunks → `regObjs` → FMEA `riskReg` → flatMap reqs to PBIs |
| Live AI | `orchestratorLive(req, ctx)` | 3772–3856 | LLM agents via `buildPrompts()` + `callLLM()`; JSON parse decomp → `applyQualityControls()` |
| Orchestration | `orchestratorDemo()` | 3652–3766 | Step UI via `setStep()` over `PIPELINE_STEPS` |
| Prefix | `autoPrefix()` | 2979–3011 | System/framework/library-derived PBI id prefix |
| Type mapping | `FW_TYPE` in demo | 3297–3298 | `business-control` → BOI+ACCEPT+INVEST+3C; etc. |

**PBI object fields (post-normalization):** `id`, `title`, `type`, `story`, `regulation`, `section`, `regRef`, `boi`, `invest`, `ac`, `accept`, `gamp`, `phase`, source metadata, `validationRubric`, `qc`.

**Gap vs future SYNTHESIZE:** No explicit `obligations`, `control_objectives`, `evidence`, `gap/risk/remediation` blocks. No `IT_DEVELOPMENT` / `IT_CONFIGURATION` gating for IT-only PBIs (not present in codebase).

### 1.5 Acceptance-criteria generation

| Source | Lines | Behavior |
|--------|-------|----------|
| Demo engine | 3369–3373 | Three Given/When/Then strings per PBI from chunk req + client context |
| Live prompts | `buildPrompts().decomposition` | 3142–3187 | Schema requires `ac[]` GWT + `accept{action,criteria,expected,pass_fail,traceable}` |
| Normalization | `normalizeStoryOutput()` | 2600–2631 | Mirrors `ac` ↔ `acceptanceCriteria` |
| Rubric check | `scoreValidationRubric()` | 2648–2650 | `ac_quality`: ≥2 AC, ≥1 full GWT |

**Rendering:** `renderStories()` expander (3971–3987) shows AC list + ACCEPT block.

### 1.6 Scoring / rubric logic

| Function | Lines | Checks (weights) |
|----------|-------|------------------|
| `scoreValidationRubric(story, scope)` | 2633–2672 | traceability (15), citation+SME approval (15), ACCEPT (15), INVEST (10), GWT AC (15), scope/jurisdiction (15), semantic quality (15) |
| `applyQualityControls()` | 2761–2832 | Orchestrates dedupe, scope cap, normalization, per-item rubric, `qcReport`, `toFdaClinicalStandardPackage()` |
| `suppressDuplicateStories()` | 2581–2598 | Jaccard ≥ 0.72 or same clause fingerprint |

**Hard gate:** `citationVerified && sourceApproved && semanticOk && scopeOk && jurOk` — caps score at 69 if fail (`2660–2661`).

### 1.7 Table rendering

MARAS does **not** use an HTML `<table>` for PBIs. Results are **story cards**:

| Function | Lines | Output |
|----------|-------|--------|
| `renderStories(stories, pipelineResult)` | 3895–3996 | QC banner + per-PBI cards: title, tags, story, source excerpt, BOI, INVEST, rubric, expandable AC |
| `buildStepBar()` / `setStep()` | 3530–3579 | Pipeline progress bar + expandable step detail cards |
| Compare matrix | `renderCompareMatrix()` | 4314–4326 | `<table class="cmp-matrix">` for Global Compare tab only |
| Readiness / SOP | `buildReadinessView()`, `mapSopToRegulations()` | 4513+, 4672+ | Grid layouts, not PBI table |

### 1.8 Export logic

| Function | Lines | Format |
|----------|-------|--------|
| `dlJira()` | 4077–4084 | CSV — `DRAFT-MARAS-Business-PBI-Jira-Export.csv` |
| `dlADO()` | 4085–4094 | CSV — `DRAFT-MARAS-Business-PBI-ADO-Export.csv` |
| `dlJSON()` | 4095–4112 | JSON — `DRAFT-MARAS-Backlog.json` + `qualityControl` additive |
| `dlFdaClinicalSchema()` | 4113–4126 | JSON — `DRAFT-MARAS-FDA-Clinical-Standard-Package.json` |
| `savePackage()` / `loadPackage()` | 4027–4071 | `localStorage` key `pkg_*` |
| `dlAssuranceReport()` | 5104+ | Assurance validation JSON |
| Compare / Readiness / CTD | 4378+, 4736+, 5005+ | Separate tab exports |

All exports watermark `DRAFT_NOT_CONTROLLED` / `packageStatus:'DRAFT_NOT_CONTROLLED'`.

---

## 2. Divergence: `apps/web` backend vs single-file MVP

| Aspect | `index.html` (MVP) | `apps/web` + `apps/api` |
|--------|-------------------|-------------------------|
| Purpose | PBI / assurance package generator | CTD/eCTD, evidence review, dossier export, story-map workspace |
| Runtime | Browser-only, no server | Next.js + FastAPI + PostgreSQL |
| Corpus | Embedded `GXP_CHUNKS` | API document store, evidence records |
| PBI generation | `runDemoEngine` / `orchestratorLive` | **Not implemented** |
| Graph data | Inline JS constants | `docs/workflows/platform-workflows.json` (workflow registry, not RAG corpus) |

**Plan implication:** RAG Graph Phase 1–5 targets **`index.html` only**. Platform backend may later host vector retrieval (OKF pipeline agent at `.cursor/agents/okf-document-pipeline.md`) but must not be required for MVP RAG Graph.

---

## 3. Existing graph / feature-flag / test patterns

### Graph data files

- **None** for RAG corpus. Closest artifacts:
  - `docs/workflows/platform-workflows.json` — Graphify workflow strings + API route refs
  - `docs/harness/platform-harness-config.json` — CRS harness config mirror
  - Mermaid in comments (`index.html` ~2835 ingest gate)

### Feature-flag patterns

| Pattern | Location | Notes |
|---------|----------|-------|
| `demoMode` toggle | `setMode()` ~1957 | Demo vs Live AI — **not** a RAG flag |
| `localStorage` prefs | `maras_guide_dismissed_v641_alignment`, `maras_sidebar_width`, `pkg_*` | UI persistence only |
| `QC_CONFIG` constants | 2323–2331 | Tunable thresholds, not user-facing flag |
| `LIVE_HARNESS_CONFIG` | 3028–3050 | Per-model token profiles (deepseek, glm compact) |

**Phase 4 legacy preservation** should add e.g. `localStorage.maras_rag_graph_v1` or URL param `?rag=1`, default **off** (legacy path unchanged).

### Test infrastructure

| Script | Purpose |
|--------|---------|
| `p0-regression.mjs` | Static HTML assertions (~70 checks) — primary gate |
| `qc-compat-regression.mjs` | VM-extracts QC block + `GXP_CHUNKS`; tests rank/dedupe/rubric without browser |
| `scripts/verify-all.mjs` | Runs all regression scripts |
| `.cursor/environment.json` | Cloud Agent install runs p0 + qc-compat |

**No Playwright/browser E2E** for single-file app. Manual: static preview `http://127.0.0.1:8080/index.html`.

---

## 4. CRS mode → minimal modular client-side functions

Per `Agents.md` and `LIVE_HARNESS_CONFIG`:

| Pillar | Maps to RAG Graph | Proposed module (Phase 1) |
|--------|-------------------|----------------------------|
| **Caveman** | Smallest stage functions, no framework | `ragParse()`, `ragRetrieve()`, … pure functions returning JSON |
| **RTK** | Each stage → MVP ID + regression fixture | Extend `qc-compat-regression.mjs` with stage snapshots |
| **Supermemory** | Reuse `H`, `rankChunks`, `GXP_CHUNKS` | Stage I/O stored on `H.ragReplay`; no duplicate corpus |
| **Graphify** | UI copy + replay panel | `Parse → Retrieve → ReRank → Synthesize → Verify → Replay` |

**Token optimization (existing):**

- `buildHarnessContextLine(H.ctx)` — compact ctx (~280 chars)
- `buildScopedSourceSummary(req, n)` — top-N chunk summaries only at decomp
- `getPrevOutputLimit(profile, stepId)` — truncated prior agent output
- `omitContextInSystemPrompt` for deepseek/glm profiles

**Proposed `H.ragReplay` shape:**

```javascript
H.ragReplay = {
  enabled: false,
  stages: {
    parse: { at, input, output, ms },
    retrieve: { at, chunks, scope, ms },
    rerank: { at, labeled, ms },
    synthesize: { at, stories, ms },
    verify: { at, qcReport, ms }
  }
};
```

---

## 5. Minimal change approach — RAG Graph mapping

### Stage mapping (current → target)

| Stage | Current functions | Change |
|-------|-------------------|--------|
| **PARSE** | `validateMvpInputs`, `parseRequirementPayload`, intake prompt / demo `regObjs` | Extract structured fields (`system`, `jurisdiction`, `obligation_hints`, `it_scope`) with deterministic rules first; LLM intake optional |
| **RETRIEVE** | `resolveScopeControls`, `rankChunks` (filter+score) | Split: retrieve = scope filter + candidate set; cap at `maxScopedChunks` |
| **RERANK** | `scoreSourceRelevance`, `applyJurisdictionFilter` | Add label taxonomy: `primary`, `supporting`, `contextual`, `suppressed`, `not_applicable` |
| **SYNTHESIZE** | `runDemoEngine` story flatMap, `orchestratorLive` decomp | Emit obligations, control objectives, evidence, gap/risk/remediation; IT PBI only if `IT_DEVELOPMENT` \| `IT_CONFIGURATION` |
| **VERIFY** | `applyQualityControls`, `scoreValidationRubric` | Add scope-consistency + traceability rules; surface in Quality Gate panel (Phase 3) |
| **REPLAY** | `PIPELINE_STEPS`, `setStep`, `toggleCard` | Per-result pipeline toggle showing stage I/O (Phase 2) |

### Proposed insertion point (minimal diff)

```text
doGenerate()
  → [NEW] if (ragGraphEnabled) H.ragReplay = runRagGraph(req, H.ctx)
  → else existing orchestratorDemo / orchestratorLive
```

`runRagGraph()` internally calls extracted stage functions, then delegates synthesis tail to existing `applyQualityControls` + `renderStories`.

### Functions/files to change (future phases)

| Priority | File | Functions / lines | Change type |
|----------|------|-------------------|-------------|
| P1 | `index.html` | New block after `QC_CONFIG` (~2331) | Add `RAG_GRAPH_CONFIG`, stage pure functions |
| P1 | `index.html` | `rankChunks` (2955–2976) | Split retrieve vs rerank; return labels |
| P1 | `index.html` | `doGenerate` (3591–3649) | Branch on feature flag |
| P2 | `index.html` | `renderStories` (3895–3996) | Pipeline replay toggle per card |
| P3 | `index.html` | After QC banner (~3911) | Quality Gate panel, INVEST regen hook |
| P4 | `index.html` | `setMode` / init (~1957, 1526) | Feature flag toggle UI |
| P5 | `qc-compat-regression.mjs` | New fixtures section | 4 fixtures + scoring rubric |
| P5 | `p0-regression.mjs` | New checks | Flag default off, stage exports |

### Files NOT to modify (Phases 1–5 for PBI path)

- `apps/api/**`, `apps/web/**` (platform stack)
- `docs/workflows/**` (unless RTK doc update only)
- Global Compare, Readiness, CTD, Assurance tab logic (unless VERIFY cross-check explicitly needed)
- `GXP_CHUNKS` corpus content (structure extensions only via additive fields)

---

## 6. Risk of each change

| Change | Risk | Mitigation |
|--------|------|------------|
| Split `rankChunks` | Demo/Live divergence if not shared | Single `ragRetrieve`/`ragRerank` used by both paths |
| Rerank labels | Wrong primary → bad PBIs | Default label = current score order; legacy ignores labels |
| IT scope gating | Over-filtering IT PBIs | Only suppress when `it_scope` explicitly non-IT; fixture coverage |
| Synthesize schema expansion | Export breakage | Additive fields; `normalizeStoryOutput` preserves legacy |
| Quality Gate regen | Token cost / provider errors | Opt-in button; demo path unchanged |
| Feature flag | Users see different behavior | Default off; banner shows active path |
| Replay UI | DOM bloat / perf | Collapsed by default; store summaries not full prompts |
| VM regression extraction | Fragile line anchors | Tag blocks with `/* RAG_GRAPH_START */` sentinels in Phase 1 |

---

## 7. Rollback plan (global)

1. **Feature flag off** — `ragGraphEnabled = false` restores `orchestratorDemo` / `orchestratorLive` exactly.
2. **Git revert** — single commit per phase; no schema migrations (client-only).
3. **Regression gate** — `node p0-regression.mjs && node qc-compat-regression.mjs` must pass before merge.
4. **Export compatibility** — golden JSON compare on `loadProductGradeSample` → generate → `dlJSON` payload shape.
5. **User packages** — `localStorage pkg_*` unchanged; new fields optional on stories.

---

## 8. Future phase checklists

### Phase 1 — Extract stage interfaces (Parse + Retrieve)

#### 1. Understanding
- [ ] Read `resolveScopeControls`, `rankChunks`, `validateMvpInputs`, `H` harness state
- [ ] Confirm default behavior with flag off matches current `p0-regression` counts

#### 2. Files to modify
- [ ] `index.html` — add `RAG_GRAPH_CONFIG`, `ragParse()`, `ragRetrieve()`, `runRagGraph()` stub
- [ ] `qc-compat-regression.mjs` — stage unit tests

#### 3. Files NOT to modify
- [ ] `apps/**`, corpus text in `GXP_CHUNKS`, export column headers

#### 4. Data-model impact
- [ ] Add `H.ragReplay` (optional); extend chunk `_qc` with `retrieveRank` only

#### 5. UI impact
- [ ] None visible (flag off)

#### 6. Security impact
- [ ] None — no new network calls

#### 7. Test plan
- [ ] `node qc-compat-regression.mjs` — retrieve count ≥ 1 for LIMS fixture
- [ ] `node p0-regression.mjs` — all existing checks pass
- [ ] VM: `ragParse(loadProductGradeSample inputs)` → structured fields

#### 8. Rollback plan
- [ ] Remove `RAG_GRAPH_*` block; delete flag branch in `doGenerate`

---

### Phase 2 — ReRank labels + Replay UI toggle

**Status (2026-09-04):** Implemented in `index.html`.

- Collapsible **Pipeline replay (optional)** under each PBI card (collapsed by default)
- Expanded view shows Parse, Retrieve (with hybrid route log + source rows), ReRank (labeled sources), Synthesis inputs, Verify warnings
- Replay controls wired to `H.ragReplay.userOverrides`:
  - `forceInclude` / `exclude` per source (Force / Exclude / Clear)
  - `scopeCats` category chips (A–H)
  - `verifyDecisions` accept/reject per warning
  - **Regenerate synthesis (draft)** re-runs Retrieve → ReRank → Synthesize → Verify
- Quality Gate panel remains visible (Phase 3); Live AI **Regenerate improved version** unchanged

See also: [hybrid-retrieval-architecture.md](./hybrid-retrieval-architecture.md) (Phase 1 retrieval).

#### 1. Understanding
- [ ] Label rules: primary = top score in-jurisdiction; suppressed = `applyJurisdictionFilter` dropped; not_applicable = domain mismatch

#### 2. Files to modify
- [ ] `index.html` — `ragRerank()`, `renderStories` replay panel, CSS for pipeline toggle

#### 3. Files NOT to modify
- [ ] `buildPrompts` (until Phase 3), platform apps

#### 4. Data-model impact
- [ ] Chunk `_qc.label` enum; `H.ragReplay.stages.rerank`

#### 5. UI impact
- [ ] Collapsible “Pipeline replay” under each PBI card; step timestamps

#### 6. Security impact
- [ ] Replay must not expose API keys; redact `callLLM` payloads in live mode

#### 7. Test plan
- [ ] Manual: generate demo package → expand replay on PBI 1 → verify 6 stages listed
- [ ] Regression: rerank labels sum to candidate count

#### 8. Rollback plan
- [ ] Hide replay UI via flag; keep labels internal only

---

### Phase 3 — Synthesize expansion + Quality Gate panel

**Status (2026-09-04):** Implemented.

- `buildQualityGateSummary()` — Pass/Needs improvement, weak INVEST list, quality flags
- `scoreRagPipelineRubric()` — 13-dimension scoring for fixtures
- `ragVerify()` — scope, traceability, AC, and quality-rule validation
- Quality Gate panel per PBI; optional Live AI regenerate (no auto-rewrite)

---

### Phase 4 — Legacy preservation feature flag

**Status (2026-09-04):** Implemented (default ON; legacy via toggle/`?rag=0`).

- `ragRetrieve()` fallback to `rankChunks()` with `fallbackUsed` banner
- Export metadata: `pipeline.ragGraphEnabled`, `pipeline.pipelineMode`
- Legacy PBI card format unchanged

---

### Phase 5 — Fixtures + scoring rubric tests

**Status (2026-09-04):** Implemented.

Fixtures: `scripts/fixtures/rag-graph/*.json` (generic IT, GxP lab, FDA clinical, QA CAPA)

Manual validation:
1. Open `index.html` → generate with RAG ON → Quality Gate + Pipeline replay
2. `?rag=0` → legacy ranking; export shows `pipelineMode: legacy`
3. `node p0-regression.mjs && node qc-compat-regression.mjs`

Known limitations: TF-IDF pseudo-vector only; heuristic graph; all output DRAFT_NOT_CONTROLLED.

Rollback: `?rag=0` or `git revert` RAG commits on `main`.

---

## 9. Recommended next phase

**Phases 0–5 complete for `index.html` MVP.**

Optional: precomputed embeddings, curated regulatory KG, bridge to `apps/web` story-map exports.

---

## 10. References

| Artifact | Path |
|----------|------|
| Single-file app | `index.html` |
| CRS / Graphify defaults | `Agents.md` |
| MVP RTK matrix | `README.md` |
| Harness config | `docs/harness/platform-harness-config.json` |
| Workflow registry | `docs/workflows/platform-workflows.json` |
| Primary regression | `p0-regression.mjs` |
| QC VM regression | `qc-compat-regression.mjs` |
| OKF pipeline (future backend RAG) | `.cursor/agents/okf-document-pipeline.md` |

---

*Phases 0–5 complete (2026-09-04). CRS RAG Graph pipeline active by default on `index.html`.*
