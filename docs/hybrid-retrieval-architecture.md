# Hybrid Retrieval Architecture (Phase 1)

**Repository:** MARAS v6.4.1 MVP (`index.html`)  
**Status:** Implemented — client-side MVP  
**Date:** 2026-09-04  

---

## Overview

MARAS Phase 1 extends the RAG Graph pipeline with a **Deterministic First** hybrid retrieval layer that combines:

1. **OKF v0.2-shaped document trees** (in-memory adapter from `GXP_CHUNKS`)
2. **Graph RAG** (bounded traversal over regulatory relationships)
3. **Vector RAG** (client-side TF-IDF cosine pseudo-vectors)

All routes merge into the existing `ragRerank()` → `ragSynthesize()` → `ragVerify()` stages. Legacy `rankChunks()` remains the fallback when RAG is disabled or hybrid retrieval throws.

---

## Routing order (Deterministic First)

```text
hybridRetrieve(parsed, req, scope)
  1. DETERMINISTIC — scope filters + explicit_refs + OKF node match
  2. GRAPH        — bounded BFS from top deterministic seeds (if low confidence, ambiguities, or explicit refs)
  3. VECTOR       — TF-IDF cosine over in-scope chunks (skipped when explicit refs + enough deterministic hits + not vague)
  4. MERGE        — dedupe by source_id, union provenance, cap at hybridMaxCandidates (20)
```

### Routing rules

| Condition | Behavior |
|-----------|----------|
| `explicit_refs` present (§11.10, Part 11, Annex 11, ALCOA, ICH E6, CAPA, …) | Deterministic boost + OKF anchor match; graph expansion from seeds |
| `det.count >= 4` + explicit refs + requirement length ≥ 80 | Vector stage **skipped** (`skipped-explicit-refs`) |
| Low deterministic confidence (< 70) or ambiguities | Graph expansion invoked |
| Vague / short requirement (< 80 chars) or semantic gap | Vector stage runs (`tfidf-cosine-pseudo`) |
| Token budget | `maxRetrieve: 16` after merge; `hybridMaxCandidates: 20` pre-rerank |

---

## OKF v0.2 adapter

`ensureHybridIndices()` lazily builds:

- **Documents:** grouped by `sourceKey` / regulation with `okfVersion: '0.2'`, authority, jurisdiction, effective date
- **Nodes:** one per chunk — `anchor`, `path`, `scopeTags`, `chunkRef`
- **No external OKF JSON file** — adapter converts embedded corpus at runtime

OKF improves deterministic routing via `hybridOkfMatch()` (anchor/path/scope tag scoring).

---

## Graph RAG

In-memory graph from `GXP_CHUNKS`:

| Edge type | Rule |
|-----------|------|
| `cites` | Same `sourceKey` (intra-document) |
| `related_process` | Shared category + ≥2 shared keywords; optional `SOP_CHUNK_LIBRARY_LINKS` |
| `implements` | Jaccard similarity > 0.42 on requirement text |

Traversal: BFS depth ≤ `graphMaxDepth` (2), expand ≤ `graphMaxExpand` (6) nodes.

---

## Vector RAG (limitation)

**No external embedding API.** `hybridVectorRetrieve()` uses **TF-IDF + cosine similarity** over chunk text (title, reg, sec, reqs, kws). Labeled `tfidf-cosine-pseudo` in route log and provenance.

Precomputed embedding JSON is not present in the repo; add `data/okf-regulatory-index.json` or embedding vectors in a future phase if semantic recall must improve.

---

## API shape

```javascript
hybridRetrieve(parsed, req, scope) → {
  route_log: [{ stage, method, count, confidence }],
  candidates: [{ chunk, cite, relevanceScore, provenance: ['deterministic'|'graph'|'vector'] }],
  provenance: { [source_id]: string[] },
  hybrid: true,
  vectorNote: 'Client-side TF-IDF cosine pseudo-vector; no external embedding API'
}
```

`ragRetrieve()` wraps `hybridRetrieve()` when `ragGraphEnabled` is true.

---

## UI

Pipeline replay panel (`ragReplaySummaryHtml`) shows:

- Hybrid route log per stage
- Provenance badges (`deterministic` / `graph` / `vector`)
- Sample merged candidates

---

## Configuration (`RAG_GRAPH_CONFIG`)

| Key | Default | Purpose |
|-----|---------|---------|
| `hybridMaxCandidates` | 20 | Pre-rerank merge cap |
| `deterministicMinBeforeVector` | 4 | Skip vector when enough deterministic hits + explicit refs |
| `graphMaxDepth` | 2 | Graph BFS depth |
| `graphMaxExpand` | 6 | Max graph-expanded nodes |
| `vectorTopK` | 8 | Vector route top-k |

---

## Tests

- `p0-regression.mjs` — static checks for hybrid functions, OKF adapter, UI badges, docs
- `qc-compat-regression.mjs` — VM tests: explicit refs → deterministic; graph expansion; vector stage on vague queries; provenance on all candidates; 4 RAG fixtures unchanged

---

## Manual validation

1. Open `index.html` — confirm RAG toggle is ON (default).
2. Load product-grade sample; generate PBIs with Part 11 requirement.
3. Expand **Pipeline replay** on a story card — verify Hybrid Retrieve route log and provenance badges.
4. Disable RAG (`?rag=0`) — confirm legacy ranking path unchanged.
5. Run: `node p0-regression.mjs && node qc-compat-regression.mjs`

---

## Rollback

1. **Runtime:** `localStorage.setItem('maras_rag_graph_v1', '0')` or `?rag=0`
2. **Git:** `git revert <hybrid-commit>` on `main`
3. **Partial:** set `ragGraphEnabled = false` default in `index.html` (reverts to legacy retrieve only)

---

## Known limitations

- TF-IDF pseudo-vector is not true semantic embedding; vague queries may return low vector counts.
- Graph edges are heuristic (same-source, keyword overlap, Jaccard) — not a curated regulatory knowledge graph.
- OKF trees are runtime-derived; no versioned OKF export/import pipeline.
- Multi-document analysis is limited to embedded + ingested chunks in the single-page corpus.
- All output remains **Draft**; SME/QA review required — no autonomous compliance claims.

---

## Related documents

- [rag-optimization-plan.md](./rag-optimization-plan.md) — Phase 0 discovery and Phase 1 roadmap
