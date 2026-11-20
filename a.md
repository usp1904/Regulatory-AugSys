# MARAS Agentic Graph RAG — Build Sequence and Delivery Status

**Repository:** `usp1904/Regulatory-AugSys`  
**Implementation branch:** `feature/maras-agentic-graph-rag`  
**Baseline:** `main`  
**Plan owner:** Product / Engineering  
**Last updated:** 2026-11-20  
**Status:** Zero-budget local indexing and retrieval implementation added to feature branch; PR #46 remains draft. CI verification is running. Local SQLite + BM25 + provenance-linked graph does not require cloud credentials. This is not yet a production Agentic Graph RAG deployment.

**Working branch:** `feature/maras-agentic-graph-rag`  
**Pull request:** https://github.com/usp1904/Regulatory-AugSys/pull/46  
**Initial branch head:** `1354cd51344b002ee61f896d0b5203bc2f1cc071`

---

## 1. Product decision

Build the Regulatory Intelligence capability inside the existing MARAS Next.js + FastAPI application. Do not rebuild the existing MARAS landing page, document repository, regulatory truth workflow, obligation review, evidence management, clarification queue, requirements mapping, CTD workflow, dossier export, or audit trail.

The new capability is an intelligence layer over MARAS's existing controlled documents and domain services.

### Target user workflow

Existing MARAS document  
→ version/hash-aware processing  
→ structure-aware extraction  
→ hierarchical regulatory chunks  
→ entity and relationship extraction  
→ persistent vector, lexical and graph indexes  
→ intent classification and query planning  
→ hybrid + graph retrieval  
→ evidence assembly  
→ grounded synthesis  
→ citation/claim validation  
→ existing MARAS obligation, interpretation, mapping and SME-review workflows.

The system must not treat an uploaded document as an authoritative regulatory source automatically. Existing source-verification and interpretation gates remain authoritative.

## 2. Repository baseline inspected

The following existing code was inspected before changes:

### Existing application

- `apps/web`: Next.js 15 application and existing navigation shell.
- `apps/api`: FastAPI application and API v1 router.
- `apps/api/app/services/document_storage.py`: controlled original-file storage and validation.
- `apps/api/app/services/document_ingestion.py`: SHA-256, deduplication, versioning, extraction orchestration and audit.
- `apps/api/app/services/document_extraction.py`: current PDF, DOCX and TXT text extraction.
- `apps/api/app/services/regulatory_truth.py`: source verification and interpretation workflow.
- `apps/api/app/services/obligation_extraction.py`: deterministic rule-based obligation extraction and SME review.
- `apps/api/app/services/requirements_mapping.py`: requirement mapping and review.
- `apps/api/app/services/evidence.py` and `evidence_queries.py`: evidence workflows.
- `apps/api/app/services/clarifications.py`: clarification workflow.
- `apps/api/app/services/audit.py`: audit events.
- `apps/api/app/models/document.py`: existing document, page and paragraph records.
- `apps/web/components/site-shell.tsx`: existing application navigation.
- `index.html`: existing static MARAS browser application and client-side RAG/trace prototypes.

### Important baseline limitation

The current browser implementation's hybrid retrieval is a client-side prototype. Its TF-IDF-like vectors and heuristic graph traversal are not a persistent, production Graph RAG service. The repository inspected does not contain a separate, complete production multimodal Agentic Graph RAG framework matching all eight stages in the architecture diagram.

The architecture diagram is a target design, not proof that those services already exist. Do not report missing modules as completed.

## 3. Non-duplication rules

1. Reuse the existing `Document`, `DocumentPage`, and `DocumentParagraph` records. Do not create a second document repository.
2. Reuse existing document hash, version, storage and audit behaviour.
3. Reuse `regulatory_truth.py` for source authority and interpretation gates.
4. Reuse `obligation_extraction.py` as the deterministic baseline. Add AI/Graph RAG as a selectable strategy; do not replace the baseline.
5. Reuse existing obligation review, clarification, requirements mapping, evidence, CTD and dossier workflows.
6. Store index metadata and query traces separately from business records. Store vectors/graph data in dedicated adapters.
7. Keep the legacy `index.html` experience operational. Add the new capability to `apps/web`.
8. Never expose provider secrets to the browser.
9. Every retrieved evidence item must resolve to a document ID, version, SHA-256, source location and exact excerpt.
10. AI outputs are candidates for human review, not legal determinations or compliance certification.

## 4. Target architecture

### Application layer
- Existing Next.js shell.
- New `/regulatory-intelligence` workspace.
- Server-side Next.js API proxy for protected calls.
- Evidence panel, retrieval trace, graph exploration, obligation results and indexing status.

### API layer
- Existing FastAPI application.
- New `/api/v1/regulatory-intelligence` router.
- Typed request/response contracts.
- Existing MARAS database session and source records.
- Existing authorization controls reused for initial integration; centralize shared auth before external production deployment.

### Intelligence services
- Ingestion adapter: consumes existing document IDs and versions.
- Parser adapter: extracts layout, text, tables, figures and OCR assets.
- Chunker: creates hierarchical, modality-aware chunks.
- Enrichment: extracts entities, concepts, obligations and relationships.
- Indexing coordinator: creates versioned manifests and retries.
- Graph store adapter: persistent entities and edges with provenance.
- Vector store adapter: embeddings and semantic retrieval.
- Lexical adapter: exact clause and keyword retrieval.
- Retrieval fusion: merge, deduplicate and rerank results.
- Orchestrator: typed, bounded agent workflow.
- Evidence assembler: creates source-backed evidence packs.
- Validator: checks citations, claim support, source status and abstention conditions.
- Observability: trace IDs, stage timings, token/cost data, failure and evaluation metrics.

### Production control plane
- Identity and tenant authorization.
- Document-level permission filters applied before retrieval.
- Secrets and key management.
- Model registry/routing and prompt versioning.
- Rate limits, quotas and cost controls.
- Durable jobs, retries and dead-letter handling.
- Retention, deletion propagation and backups.
- Audit and observability.

## 5. Technology decisions and constraints

Preferred direction already discussed for MARAS:
- Existing Next.js + FastAPI + PostgreSQL.
- Zero-budget MVP: Python standard-library SQLite sidecar under existing STORAGE_ROOT, BM25 ranking and NetworkX-compatible graph abstraction (current persisted graph uses SQLite tables; no NetworkX dependency is needed yet).
- Do not require Google Vertex AI, Firebase/Firestore or any paid service for local development and demonstration.
- Keep Vertex AI/Firestore as optional adapters for a later sponsor-funded deployment.
- Do not introduce Neo4j for the MVP.
- A Firestore entity/edge model is not a native graph database. Benchmark bounded adjacency traversal and query scale. Keep graph storage behind an interface so a dedicated graph store can be introduced later without changing MARAS workflows.
- OCR may use Google Document AI, subject to credentials, regional availability, data residency, and cost approval.
- Evaluate Docling for structure-aware parsing; do not add it until the deployment image and representative regulatory documents pass tests.
- Begin with an explicit Python state machine and typed tool contracts. Add a framework only if it solves a demonstrated orchestration need.
- Zero-budget baseline must run locally without cloud credentials or paid model APIs: SQLite persistence, BM25 ranking and source-linked graph facts.
- Use a durable queue/worker for production indexing. Do not rely on FastAPI in-process background tasks for long-running indexing.

No provider key, project ID, Firebase database, production tenant model or deployment target was supplied during this implementation. External provider integrations therefore remain gated, not falsely marked complete.

## 6. Build sequence

### Phase 0 — Repository baseline and architecture
- [x] Inspect repository tree and current API/UI boundaries.
- [x] Inspect document ingestion, extraction, obligations, regulatory truth, evidence, mapping and audit services.
- [x] Confirm existing Next.js + FastAPI application is the production integration surface.
- [x] Create isolated feature branch.
- [x] Create this build/status record.
- [ ] Identify and inspect the separate framework source repository if one exists.
- [ ] Freeze provider choices and environment requirements.

### Phase 1 — Thin vertical slice: source-grounded retrieval
- [x] Add a separate Regulatory Intelligence navigation entry.
- [x] Add a focused Regulatory Intelligence workspace.
- [x] Add typed retrieval request/response contracts.
- [x] Add deterministic source-grounded retrieval against existing extracted MARAS documents.
- [x] Return source document ID, version, hash, page/paragraph location and exact excerpt.
- [x] Route protected frontend requests through a server-side proxy.
- [ ] Add and run automated tests in the repository environment.
- [ ] Validate access control and browser/API integration.
- [ ] Demo with a representative approved regulatory source.

**Scope note:** The initial lexical-only slice has since been extended by Phase 1.5 and Phase 1.6 below. This initial slice remains the baseline compatibility path.


### Phase 1.5 — Modular intelligent retrieval engine (implemented; verification pending)
- [x] Add stable source-addressable chunks over existing MARAS Document/Page/Paragraph records.
- [x] Add transparent candidate entity extraction for regulatory references, controls and processes.
- [x] Add provenance-linked co-mention graph edges referencing source chunk IDs.
- [x] Add hybrid retrieval service with lexical ranking, optional Vertex AI embeddings and reciprocal-rank fusion.
- [x] Add optional Firestore vector, entity and edge persistence adapters.
- [x] Add document listing and explicit index operation endpoints.
- [x] Add document selection and indexing controls to Regulatory Intelligence workspace.
- [x] Enforce current document version and SHA-256 when filtering persistent vector results.
- [ ] Configure GCP project, Vertex AI access, Firestore database and vector index.
- [ ] Run CI and backend/frontend regression suites after latest commit.
- [ ] Validate retrieval against SME-labelled regulatory question set.

**Current limitation:** With `RAG_ENABLED=false` (default), the service runs source-grounded lexical retrieval plus per-query candidate graph expansion from MARAS text. It does not persist a graph or vectors. With `RAG_ENABLED=true`, the optional Vertex AI + Firestore adapters embed and persist chunks/entities/edges and query Firestore vector search. Firestore vector index creation, credentials, billing, IAM, regional/data-residency approval and integration tests remain deployment prerequisites. Graph extraction currently emits deterministic co-mention candidate edges, not validated legal relationships. Do not present these edges as authoritative regulatory logic.


### Phase 1.6 — Query planning and inspectable orchestration (implemented; verification pending)
- [x] Add deterministic query intent classification for clause lookup, relationship analysis, obligation retrieval and general regulatory retrieval.
- [x] Add bounded retrieval plan with explicit strategies and one-hop graph limit.
- [x] Add orchestration endpoint returning plan, retrieval mode, stage trace and evidence.
- [x] Route the Regulatory Intelligence workspace through the orchestrated query endpoint.
- [ ] Add model-backed generation only after claim/evidence validation and source-authority checks are implemented.

**Current product behaviour:** The new engine indexes extracted MARAS documents on demand, then performs lexical retrieval and local graph expansion. If the optional cloud mode is configured, it also uses Vertex AI embeddings, Firestore vector search and persistent Firestore graph edges. The orchestrator currently plans and coordinates retrieval; it does not yet invoke autonomous LLM agents or generate answers.


### Phase 1.7 — Zero-budget persistent local retrieval (implemented; CI pending)
- [x] Add a persistent SQLite sidecar index under existing MARAS STORAGE_ROOT.
- [x] Persist source-addressable chunks and sparse term-frequency data.
- [x] Persist candidate entities and provenance-linked co-mention edges.
- [x] Add dependency-free BM25 scoring and reciprocal-rank fusion with graph expansion.
- [x] Filter indexed chunks against current MARAS document version and SHA-256.
- [x] Replace a document's prior index atomically during re-indexing.
- [x] Keep cloud providers optional and disabled by default.
- [x] Add tests for local persistence, retrieval, stale versions and BM25 ranking.
- [ ] Complete CI and review latest workflow results.
- [ ] Run end-to-end test with real MARAS source documents in local environment.

**Zero-budget boundary:** The local engine currently uses BM25, not dense semantic embeddings. It is a persistent lexical + graph retrieval baseline. Local embedding models, OCR, multimodal extraction and answer generation are subsequent increments and must be selected based on actual machine resources and evaluation results.


### Phase 1.8 — Evidence-only synthesis and citation validation (implemented; CI pending)
- [x] Add extractive sentence selection from retrieved evidence passages.
- [x] Require every displayed claim to match verbatim text in its source excerpt.
- [x] Attach document ID, version, SHA-256, page location and chunk ID to each claim citation.
- [x] Abstain when no source sentence can be safely selected.
- [x] Display evidence-only synthesis and citations in the Regulatory Intelligence workspace.
- [ ] Complete CI verification and test the full UI/API flow with real MARAS documents.

**Safety boundary:** This is extractive evidence assembly, not LLM-generated interpretation. It must not be represented as legal advice, applicability analysis or a compliance determination.

### Phase 2 — Index lifecycle and structured extraction
- [ ] Add index job and index manifest models/migrations.
- [ ] Dispatch indexing after successful existing document ingestion.
- [ ] Make jobs idempotent using document ID + version + SHA-256 + pipeline version.
- [ ] Preserve original files and existing extracted page/paragraph records.
- [ ] Add parser adapters for PDF, DOCX, HTML, PPTX and XLSX.
- [ ] Add OCR for scanned PDFs and image assets.
- [ ] Extract layout, headings, tables, figures, captions and page coordinates.
- [ ] Add hierarchical chunks: document → part/chapter → section → clause → chunk.
- [ ] Attach source coordinates, extraction confidence and pipeline version to every chunk.
- [ ] Add reprocessing and deletion propagation.

### Phase 3 — Regulatory knowledge graph
- [ ] Define versioned node/edge schema.
- [ ] Node types: source, document version, section, clause, requirement, obligation, control, policy/SOP, system/process, evidence and action.
- [ ] Relationship types: CONTAINS, EXPRESSES_REQUIREMENT, CREATES_OBLIGATION, IMPLEMENTS_CONTROL, GOVERNED_BY, AFFECTS, REQUIRES_EVIDENCE, SUPERSEDES and DEPENDS_ON.
- [ ] Extract entities and candidate relationships.
- [ ] Require source evidence for every edge.
- [ ] Add entity resolution and deduplication.
- [ ] Add graph versioning and incremental updates.
- [ ] Benchmark Firestore adjacency traversal with realistic graph sizes.
- [ ] Keep graph adapter replaceable.

### Phase 4 — Production retrieval
- [ ] Add embedding provider abstraction and Vertex AI adapter.
- [ ] Add vector index adapter and integration tests.
- [ ] Add lexical/BM25 retrieval.
- [ ] Add graph traversal retrieval with bounded depth, node and time limits.
- [ ] Add metadata filters and permission filters before retrieval.
- [ ] Add reciprocal-rank fusion or tested equivalent.
- [ ] Add reranking and dynamic top-K.
- [ ] Add evidence-pack assembly with exact source locations.
- [ ] Add retrieval trace and index-version trace.

### Phase 5 — Agent orchestration and grounded generation
- [ ] Add intent/task classifier.
- [ ] Add query planner and typed execution plan.
- [ ] Add bounded retrieval tools.
- [ ] Add specialist obligation and impact-analysis agents.
- [ ] Add synthesis agent with evidence-only context.
- [ ] Add claim-to-evidence alignment.
- [ ] Add citation validator.
- [ ] Add contradiction and source-status checks.
- [ ] Add abstain, clarify and human-escalation routes.
- [ ] Persist query traces, prompt/model versions and review decisions.
- [ ] Reuse existing obligation and interpretation review workflows.

### Phase 6 — MARAS business workflows
- [ ] Add indexing status to document detail.
- [ ] Link query results to existing obligation records.
- [ ] Link obligations to existing requirement mappings.
- [ ] Reuse clarification workflow for unresolved applicability.
- [ ] Reuse evidence workflow for control/evidence review.
- [ ] Add regulatory change comparison and impact analysis.
- [ ] Add graph explorer with source-backed edges.
- [ ] Add role-based views and audit visibility.

### Phase 7 — Production readiness
- [ ] Implement real identity, tenant and document-level authorization.
- [ ] Validate data residency, encryption and secrets management.
- [ ] Add durable worker, retry policy and dead-letter queue.
- [ ] Add model routing, prompt versioning, quotas and budgets.
- [ ] Add OpenTelemetry traces and structured logs.
- [ ] Add retention, deletion propagation, backups and restore tests.
- [ ] Build a gold evaluation set with SME-reviewed answers and evidence.
- [ ] Measure Recall@K, Precision@K, MRR/nDCG, citation correctness, obligation precision/recall, graph-path accuracy, abstention accuracy, latency and cost.
- [ ] Run security, prompt-injection, malicious-document and cross-tenant leakage tests.
- [ ] Complete UAT and release approval.
- [ ] Deploy to a controlled non-production environment before production.

## 7. File-level change register

### Existing files to reuse
- `apps/api/app/models/document.py`
- `apps/api/app/services/document_storage.py`
- `apps/api/app/services/document_ingestion.py`
- `apps/api/app/services/document_extraction.py`
- `apps/api/app/services/regulatory_truth.py`
- `apps/api/app/services/obligation_extraction.py`
- `apps/api/app/services/requirements_mapping.py`
- `apps/api/app/services/evidence.py`
- `apps/api/app/services/clarifications.py`
- `apps/api/app/services/audit.py`
- `apps/api/app/core/database.py`
- `apps/web/components/obligation-workbench.tsx`
- `apps/web/components/evidence-reviewer.tsx`
- `apps/web/components/site-shell.tsx`
- `index.html` (legacy compatibility only)

### New files added in Phase 1 and 1.5/1.6
- `apps/api/app/schemas/regulatory_intelligence.py`
- `apps/api/app/services/regulatory_intelligence.py`
- `apps/api/app/api/v1/regulatory_intelligence.py`
- `apps/api/tests/test_regulatory_intelligence.py`
- `apps/api/app/regulatory_rag/__init__.py`
- `apps/api/app/regulatory_rag/chunking.py`
- `apps/api/app/regulatory_rag/graph.py`
- `apps/api/app/regulatory_rag/providers.py`
- `apps/api/app/regulatory_rag/engine.py`
- `apps/api/app/regulatory_rag/planner.py`
- `apps/api/app/regulatory_rag/orchestrator.py`
- `apps/api/app/regulatory_rag/index_store.py`
- `apps/api/app/regulatory_rag/sparse.py`
- `apps/api/app/regulatory_rag/synthesis.py`
- `apps/api/app/schemas/regulatory_intelligence.py` (extended with index/query contracts)
- `docs/regulatory-intelligence-engine.md`
- `apps/web/app/regulatory-intelligence/page.tsx`
- `apps/web/components/regulatory-intelligence-workbench.tsx`
- `apps/web/app/api/regulatory-intelligence/retrieve/route.ts`
- `apps/web/app/api/regulatory-intelligence/documents/route.ts`
- `apps/web/app/api/regulatory-intelligence/index/route.ts`
- `apps/web/app/api/regulatory-intelligence/query/route.ts`

### Planned later files
- `apps/api/app/regulatory_rag/ingestion/*`
- `apps/api/app/regulatory_rag/graph/*`
- `apps/api/app/regulatory_rag/retrieval/*`
- `apps/api/app/regulatory_rag/agents/*`
- `apps/api/app/regulatory_rag/evidence/*`
- `apps/api/app/regulatory_rag/observability/*`
- `apps/api/app/models/rag_index_job.py`
- `apps/api/app/models/rag_index_manifest.py`
- `apps/api/alembic/versions/*_rag_indexing.py`
- `apps/api/app/workers/rag_index_worker.py`

Do not create empty placeholder modules. Add each module when its contract and tests are ready.

## 8. API contracts

Current endpoints:
- `GET /api/v1/regulatory-intelligence/documents` lists extracted MARAS source records.
- `POST /api/v1/regulatory-intelligence/index` indexes one document; writer access required.
- `POST /api/v1/regulatory-intelligence/retrieve` returns source-grounded retrieval results.
- `POST /api/v1/regulatory-intelligence/query` runs query planning and bounded retrieval orchestration, returning evidence and an execution trace.
- Access: existing MARAS mapping-reader/writer credentials for this internal workspace. The frontend uses server-side proxies; provider secrets are not sent to browser JavaScript.

Planned future endpoints:
- `POST /api/v1/regulatory-intelligence/analyze`
- `GET /api/v1/regulatory-intelligence/index-status`
- `GET /api/v1/regulatory-intelligence/documents/{document_id}`
- `POST /api/v1/regulatory-intelligence/documents/{document_id}/reindex`
- `GET /api/v1/regulatory-intelligence/traces/{trace_id}`

## 9. Definition of Done

A phase is complete only when:
- Code is implemented and committed.
- Automated tests pass in CI or a recorded local run.
- Existing MARAS tests continue to pass.
- No duplicate business records or document repository are introduced.
- Permissions are enforced before data retrieval.
- Evidence is traceable to exact document version and location.
- Failure modes and limitations are documented.
- Build status in this file is updated with commit/PR references.

A code scaffold is not a completed integration. A passing unit test is not production readiness. A generated answer is not proof of regulatory correctness.

## 10. Current delivery status

| Workstream | Status | Evidence / next action |
|---|---|---|
| Repository inspection | Complete | Existing source files and tree inspected |
| Architecture decision | Complete | Reuse MARAS services; add intelligence layer |
| Feature branch | Complete | `feature/maras-agentic-graph-rag` |
| Build plan | Complete | This file |
| Regulatory Intelligence UI | Implemented in branch | `apps/web/app/regulatory-intelligence/page.tsx`; CI pending |
| Source-grounded retrieval API | Implemented in branch | `POST /api/v1/regulatory-intelligence/retrieve`; CI pending |
| Automated tests | Added; CI running | PR #46 GitHub Actions run; record final outcome after completion |
| Chunking and persistent local index | Implemented, CI pending | SQLite sidecar, BM25 term index, source version/hash checks; manual index endpoint |
| Multimodal parsing/OCR | Not started | Phase 2 |
| Candidate graph extraction and local persistence | Implemented, CI pending | SQLite entity/edge tables; co-mention edges only |
| Vertex embeddings and Firestore vector adapter | Optional only | Not required for zero-budget MVP; requires GCP if later enabled |
| Query planner, retrieval orchestration and extractive evidence synthesis | Implemented, CI pending | `planner.py`, `orchestrator.py`, `synthesis.py`, `/query`; no LLM generation |
| Production security/observability | Not started | Phase 7 |
| Deployment | Not started | Credentials and target environment required |

### Current honest product maturity

**Phase 1.8 zero-budget evidence retrieval prototype / internal integration slice.** It has source-aware chunking, persistent local BM25 and graph indexes, version/hash-aware retrieval, deterministic query planning, extractive evidence assembly and verbatim citation validation. It does not yet provide dense semantic embeddings, multimodal extraction, durable background jobs or autonomous LLM agents. It does not generate regulatory interpretations and is not a production Agentic Graph RAG system.

## 11. Local verification commands

From repository root:

```bash
cd apps/api
pytest
ruff check app tests
```

```bash
cd apps/web
npm run typecheck
npm run build
```

Existing regression scripts, when present in the checked-out repository:

```bash
node p0-regression.mjs
node qc-compat-regression.mjs
node scripts/verify-all.mjs
```

Record the actual command output and commit SHA here after execution. Do not mark tests passed without running them.
