# MARAS Agentic Graph RAG — Build Sequence and Delivery Status

**Repository:** `usp1904/Regulatory-AugSys`  
**Implementation branch:** `feature/maras-agentic-graph-rag`  
**Baseline:** `main`  
**Plan owner:** Product / Engineering  
**Last updated:** 2026-11-20  
**Status:** Phase 1.9 implementation and its follow-up documentation/test changes are committed on the feature branch. GitHub Actions CI passed on the current branch head `7dbaf665` (run `44748618152`). PR #46 remains open as draft. Local SQLite + BM25 + provenance-linked candidate graph does not require cloud credentials. Local end-to-end UAT with real MARAS documents is still outstanding.

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


### Phase 1.7 — Zero-budget persistent local retrieval (implemented; CI passed)
- [x] Add a persistent SQLite sidecar index under existing MARAS STORAGE_ROOT.
- [x] Persist source-addressable chunks and sparse term-frequency data.
- [x] Persist candidate entities and provenance-linked co-mention edges.
- [x] Add dependency-free BM25 scoring and reciprocal-rank fusion with graph expansion.
- [x] Filter indexed chunks against current MARAS document version and SHA-256.
- [x] Replace a document's prior index atomically during re-indexing.
- [x] Keep cloud providers optional and disabled by default.
- [x] Add tests for local persistence, retrieval, stale versions and BM25 ranking.
- [x] Complete CI and review latest workflow results (current branch head `7dbaf665`, run `44748618152`, success).
- [ ] Run end-to-end test with real MARAS source documents in local environment.

**Zero-budget boundary:** The local engine currently uses BM25, not dense semantic embeddings. It is a persistent lexical + graph retrieval baseline. Local embedding models, OCR, multimodal extraction and answer generation are subsequent increments and must be selected based on actual machine resources and evaluation results.


### Phase 1.8 — Evidence-only synthesis and citation validation (implemented; CI passed)
- [x] Add extractive sentence selection from retrieved evidence passages.
- [x] Require every displayed claim to match verbatim text in its source excerpt.
- [x] Attach document ID, version, SHA-256, page location and chunk ID to each claim citation.
- [x] Abstain when no source sentence can be safely selected.
- [x] Display evidence-only synthesis and citations in the Regulatory Intelligence workspace.
- [x] Complete CI verification for the current branch head (`7dbaf665`, run `44748618152`).
- [ ] Test the full UI/API flow with real MARAS documents.

**Safety boundary:** This is extractive evidence assembly, not LLM-generated interpretation. It must not be represented as legal advice, applicability analysis or a compliance determination.


### Phase 1.9 — MARAS source-authority gate (implemented; CI passed)
- [x] Reuse existing `RegulatorySourceRecord` rather than creating a second source registry.
- [x] Attach source status to every retrieved evidence item.
- [x] Mark missing source records as `UNREGISTERED` and content-hash mismatches as `STALE`.
- [x] Permit extractive synthesis only when the MARAS source status is `VERIFIED` and the source hash matches the current document.
- [x] Keep unverified evidence visible for review while abstaining from synthesis.
- [x] Add tests for verified, unverified and stale source behaviour.
- [x] Complete CI verification for the current branch head (`7dbaf665`, run `44748618152`).
- [ ] Run the workflow against existing MARAS verified source records in a local end-to-end session.

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
- `docs/zero-budget-demo.md`
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
| Regulatory Intelligence UI | Implemented in branch; CI passed | `apps/web/app/regulatory-intelligence/page.tsx`; full real-document UAT outstanding |
| Source-grounded retrieval API | Implemented in branch; CI passed | `POST /api/v1/regulatory-intelligence/retrieve`; full real-document UAT outstanding |
| Automated tests | <span>CI passed</span> | Current branch head `7dbaf665`; GitHub Actions run `44748618152` completed successfully |
| Chunking and persistent local index | Implemented; CI passed | SQLite sidecar, BM25 term index, source version/hash checks; manual index endpoint |
| Multimodal parsing/OCR | Not started | Phase 2 |
| Candidate graph extraction and local persistence | Implemented; CI passed | SQLite entity/edge tables; co-mention edges only |
| Vertex embeddings and Firestore vector adapter | Optional only | Not required for zero-budget MVP; requires GCP if later enabled |
| Query planner, retrieval orchestration, extractive synthesis and MARAS source gate | Implemented; CI passed | `planner.py`, `orchestrator.py`, `synthesis.py`, `/query`; source status and SHA-256 gate; no LLM generation |
| Production security/observability | Not started | Phase 7 |
| Deployment | Not started | Credentials and target environment required |

### Current honest product maturity

**Phase 1.9 zero-budget evidence retrieval prototype / internal integration slice.** It has source-aware chunking, persistent local BM25 and graph indexes, version/hash-aware retrieval, deterministic query planning, extractive evidence assembly, verbatim citation validation and a gate that requires MARAS source verification. It does not yet provide dense semantic embeddings, multimodal extraction, durable background jobs or autonomous LLM agents. It does not generate regulatory interpretations and is not a production Agentic Graph RAG system.

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


## 12. Progress update policy

This file is the living build ledger for the product. Update it in the same implementation sequence as the application, not as a retrospective afterthought.

For every future implementation increment:
1. Update the relevant phase checklist and delivery-status row in this file.
2. Add a dated entry to the progress log below with the exact scope, changed files, tests/CI result, commit SHA and known limitations.
3. Update the maturity statement. Do not mark a capability complete until code, tests and required integration checks support that claim.
4. Record blockers and the next concrete action. Distinguish implemented, CI-passed, locally validated, deployed and production-ready.
5. Keep this file in the same feature branch/PR as the code it describes.

### Progress log

#### 2026-11-20 — Phase 1.9 verification and delivery ledger refresh
- Confirmed GitHub Actions CI passed on branch head `7dbaf665b9b0ae0a550f084c15a83675c7fa9f8c` (workflow run `44748618152`).
- Confirmed PR #46 remains open and in draft state.
- Updated Phase 1.7, 1.8 and 1.9 status to reflect CI success.
- Added coverage for verified, unverified and stale regulatory source behaviour; stale or hash-mismatched sources must abstain from extractive synthesis.
- Added the zero-budget local demo runbook at `docs/zero-budget-demo.md`.
- Remaining validation: run the application locally against actual MARAS regulatory documents, confirm the UI/API flow, and verify the source-record review process end to end.
- Product maturity remains an internal prototype. CI success does not establish real-document correctness, production security, deployment readiness or regulatory advice capability.


## 13. Immersive product experience — glassmorphism + modern neumorphism

### UX audit: gaps found in the original Regulatory Intelligence workspace
The original workspace was functional but visually close to a plain internal admin form. It lacked:
- A strong product identity and a clear explanation of what the intelligence workspace does.
- At-a-glance source and engine context.
- A clear separation between source selection, query execution, evidence inspection and execution transparency.
- A focused evidence explorer with source-status filtering and citation-copy affordance.
- A visible trust narrative explaining the MARAS source-authority gate and the difference between retrieved evidence and regulatory interpretation.
- Consistent visual hierarchy, responsive cards, interaction feedback and reduced-motion handling.

### Implemented in the application
- [x] Rebuilt the Regulatory Intelligence workspace as a three-view experience: Workspace, Evidence and Execution trace.
- [x] Added a dark, premium intelligence hero with a restrained luminous grid, translucent trust chip and live data summaries.
- [x] Added glass surfaces with layered translucency, blur, subtle reflective borders and soft neumorphic depth.
- [x] Added consistent typography, spacing, icon tiles, status chips, gradient primary actions and tactile secondary actions.
- [x] Added document context preview and clear source-selection state.
- [x] Added suggested regulatory questions and query character count.
- [x] Added evidence explorer with status filters (ALL, VERIFIED, UNVERIFIED, UNREGISTERED, STALE).
- [x] Added copy-citation action retaining filename, document ID, version, location, SHA-256 and excerpt.
- [x] Added extractive synthesis presentation with claim citations and disclaimer.
- [x] Added execution trace view for intent, graph hop limit, planner rationale, strategies and returned stages.
- [x] Added trust and traceability panel, capability disclosure and explicit local-first prototype boundary.
- [x] Added responsive layouts and reduced-motion preference support.
- [x] Kept the existing MARAS SiteShell and backend API contracts; no duplicate document or regulatory source registry introduced.

### Files changed
- `apps/web/components/regulatory-intelligence-workbench.tsx` — workspace, evidence and trace UX.
- `apps/web/app/globals.css` — glassmorphism/neumorphism design tokens and component styles.
- `a.md` — progress and implementation ledger.

### Validation and limitations
- Lucide icons were already present in `apps/web/package.json`; no new dependency was added.
- Existing API endpoints and request/response contracts are retained.
- GitHub Actions was triggered by the UI implementation commit; record the final workflow result before calling this milestone CI-passed.
- Browser visual QA at desktop and mobile widths remains outstanding.
- Accessibility review, keyboard-only testing, contrast measurements and cross-browser backdrop-filter fallback checks remain outstanding.
- This is a presentation and interaction improvement. It does not add autonomous agents, semantic embeddings, multimodal parsing or production security.

### Progress log — 2026-11-20
- Replaced the plain single-page workbench with Workspace / Evidence / Execution trace views.
- Added glassmorphism surfaces and modern neumorphic controls without introducing paid services or new package dependencies.
- Kept the existing API calls and MARAS source verification semantics intact.
- UI implementation commit: `ee2160ae7a3c92f357b34c1ab37f5faabd0e7061`.
- Design-system commit: `68b41bd64fc663ddfcfdacaa0543c0075fe5d978`.
- CI and real browser QA: pending confirmation.


## 14. Unified MARAS enterprise experience — intake, obligations and graph exploration

### Shared platform design
- [x] Replaced the plain navigation header with a unified MARAS Intelligence shell, product identity, workspace navigation and consistent safety banner.
- [x] Applied the frosted-glass / soft-neumorphic design system to all existing `.panel`, form, input, file upload, table, button and page-heading patterns.
- [x] Added responsive navigation, global footer, focus-visible keyboard outlines and a consistent background/surface system.
- [x] Preserved the internal-review / non-submission disclaimer throughout the platform.

### Document intake and document detail
- [x] The existing CTD Engine upload and document register now inherit the shared glass surfaces and controls.
- [x] Existing document detail, extracted text, evidence capture and audit-event cards inherit the shared system without duplicating their workflows.
- [x] Kept the existing document storage, parsing, versioning, SHA-256 and evidence capture APIs.

### Regulatory obligation review
- [x] Existing candidate extraction, status filters, SME decision capture, review rationale and mapping handoff now inherit the shared platform styling.
- [x] Kept the current obligation extraction API and review semantics; no parallel obligation register created.
- [x] Retained the clear boundary that extraction is heuristic screening and that SME review is mandatory.

### Graph exploration
- [x] Added a read-only graph endpoint for indexed document candidate entities and provenance-linked edges.
- [x] Added a protected Next.js API proxy using the existing server-side MARAS reader credential.
- [x] Added a dedicated Graph Explorer route and navigation entry.
- [x] Added an interactive SVG entity graph with entity selection and linked evidence excerpts.
- [x] Graph edges show filename, version, hash, page/chunk provenance.
- [x] Added explicit warning that graph edges are heuristic co-mentions, not validated regulatory relationships or legal interpretations.
- [ ] Add robust graph layout / clustering and cross-document relationship browsing.
- [ ] Add graph-specific API tests and end-to-end UI tests.

### Files changed in this milestone
- `apps/web/components/site-shell.tsx`
- `apps/web/app/globals.css`
- `apps/web/components/regulatory-graph-explorer.tsx` (new)
- `apps/web/app/graph/page.tsx` (new)
- `apps/web/app/api/regulatory-intelligence/graph/[documentId]/route.ts` (new)
- `apps/api/app/regulatory_rag/index_store.py`
- `apps/api/app/services/regulatory_intelligence.py`
- `apps/api/app/api/v1/regulatory_intelligence.py`
- `a.md`

### Production readiness and deployment status
- This monorepo's main branch README identifies the GitHub Pages single-file demo as the currently published MVP. The Next.js + FastAPI application is a separate stack requiring a running web service, API service, database and persistent document/index storage.
- GitHub Pages cannot host the FastAPI service or the full server-rendered Next.js + persistent local SQLite workflow as configured.
- Do not mark the product production-live merely because code is merged or GitHub Pages publishes the legacy `index.html`.
- Deployment requires a supported app host, managed PostgreSQL or durable storage, API/web environment variables, secret configuration, TLS/domain, health checks, migration execution and a persistent volume for `STORAGE_ROOT`.
- No production host/domain/credentials have been provided or verified in this task. Production deployment is therefore not claimed.
- Run CI and browser QA for the new graph endpoint and shared design before merging to main.


## 14. Product-wide experience unification and graph exploration

### Scope
Bring the shared glassmorphism / modern neumorphism system beyond the Regulatory Intelligence landing workspace. Preserve existing MARAS business flows and APIs; do not create a parallel document repository or obligation register.

### Implemented in this iteration
- [x] Replaced the shared SiteShell identity and navigation with a consistent MARAS Intelligence header, safety banner, responsive navigation and global footer.
- [x] Added common glass surfaces, frosted backgrounds, typography, form controls, primary/secondary buttons, and soft neumorphic depth to the shared global stylesheet.
- [x] Applied the shared visual language to obligation extraction and SME review cards using the existing obligation APIs and status model.
- [x] Applied the shared glass surface and input/button styling to document detail, evidence capture and CTD intake/review through shared shell and global component styles. Existing CTD markup was restored to its original validated structure after a failed markup-only transformation; no workflow logic was replaced.
- [x] Added a Graph Exploration route and shared navigation entry.
- [x] Added a bounded, authenticated graph read endpoint for currently indexed document versions.
- [x] Added a graph read service that excludes stale document-version/hash edges from the response.
- [x] Added a graph explorer that displays actual candidate entities, source-linked co-mention edges and source excerpts; selecting an entity filters connected edges.
- [x] Added explicit interpretation warning: current graph edges are heuristic co-mentions, not validated legal, causal or compliance relationships.
- [x] Documented graph route and API in README.

### Files changed in this iteration
- `apps/web/components/site-shell.tsx`
- `apps/web/app/globals.css`
- `apps/web/components/obligation-workbench.tsx`
- `apps/web/components/regulatory-graph-explorer.tsx`
- `apps/web/app/graph/page.tsx`
- `apps/web/app/regulatory-intelligence/page.tsx`
- `apps/web/app/api/regulatory-intelligence/graph/route.ts`
- `apps/api/app/regulatory_rag/index_store.py`
- `apps/api/app/services/regulatory_intelligence.py`
- `apps/api/app/api/v1/regulatory_intelligence.py`
- `README.md`

### Deployment assessment
- Repository default branch is `main`; current work is on `feature/maras-agentic-graph-rag` and PR #46.
- The existing GitHub Pages deployment is the legacy static MARAS UI. It cannot run the Next.js + FastAPI application stack.
- Vercel account context currently shows a Hobby team with a linked Saavify project, but no linked Regulatory-AugSys project.
- The web app can be deployed as a Vercel project rooted at `apps/web`, but the FastAPI service, persistent PostgreSQL database, durable document storage and production secrets still need a host/configuration. The current SQLite RAG index and uploaded-file storage are local persistent-volume paths, not safe as ephemeral serverless filesystem state.
- Do not label the product production-live until the API and durable storage are deployed, server-side API URL/reader-writer keys are configured, migrations run, and end-to-end upload → index → retrieve → obligation review → graph tests pass.

### Validation status — 2026-11-20
- GitHub Actions CI has been triggered for the graph API, graph explorer and shared design-system changes.
- Some intermediate commits have failed CI; latest verification is in progress. Inspect the latest run and fix any failure before merging.
- Browser visual QA, keyboard accessibility, real-corpus graph sanity check and hosted end-to-end smoke test remain pending.
- No production deployment has been claimed or attempted against an unconfigured API host.


### Progress update — 2026-11-20 (continued)
- Added a protected, read-only graph API for indexed document entities and source-linked candidate edges.
- Added a Next.js server-side proxy and interactive Graph Explorer page. Entity selection filters associated evidence passages.
- Added the Graph Explorer to the global navigation.
- Extended the shared design system to the existing platform shell, upload controls, panels, forms, tables and buttons.
- Updated the README with the new workspace routes and deployment constraints.
- CI exposed Ruff import-order and line-length errors in the graph API/service; corrected those formatting issues. A subsequent full CI run for the latest branch head is still running.
- Main branch has not been changed. PR #46 remains open pending CI and review.
- Vercel account discovery found no Vercel project linked to this GitHub repository. The only linked project visible is for a different repository. No production deployment was created.
- Production release remains blocked until a deployable host and durable storage/database for FastAPI, uploaded source documents and the local RAG index are configured. GitHub Pages is only the legacy static MVP and cannot host the full application stack.


### Graph endpoint hardening
- [x] Use the existing document-scoped graph endpoint `GET /api/v1/regulatory-intelligence/graph/{document_id}` rather than introducing a second graph API.
- [x] Filter returned graph edges against the current MARAS document version and SHA-256 before exposing them.
- [x] Keep graph reads behind the existing MARAS reader authorization dependency.
- [x] Route the Next.js graph proxy through the server-side reader credential and validate the document ID.
- [x] Graph Explorer now consumes the document-scoped response and renders source evidence for the selected node.

### CI remediation
- [x] Inspected failing GitHub Actions logs. Initial failure was Ruff import ordering plus line-length violations in the graph API/service additions.
- [x] Removed the duplicate graph read service and corrected import ordering.
- [x] Corrected the graph proxy's numeric document-ID validation regex.
- [ ] Confirm the latest workflow for the final feature-branch HEAD is green before merge.

### Hosting and production readiness
- The Vercel account currently has no Regulatory-AugSys project linked. Only a separate Saavify project is linked.
- Vercel can host the Next.js web application, but it does not solve the FastAPI + persistent PostgreSQL + durable uploaded-document storage requirement by itself.
- Do not merge and call this production-live solely because the web bundle deploys. Production configuration must include a reachable FastAPI URL, persistent PostgreSQL, durable object/file storage, server-only reader/writer secrets, migrations and upload/index/retrieve/review/graph smoke tests.


### Main-branch merge — 2026-11-20
- [x] Final feature-branch verification completed successfully for HEAD `3f56b9cdc9f5569946fe0e183346a75729d80d1e` (GitHub Actions run `44755497937`).
- [x] Pull request #46 marked ready and squash-merged into `main`.
- [x] Main merge commit: `cf3147e7d984785c2ca87fa6b087b5c13ea25e05`.
- [x] The unified MARAS shell, shared design system, graph explorer and authenticated current-version graph API are now in `main`.
- [ ] Production hosting is not complete. The Vercel account context had no Regulatory-AugSys project linked; no FastAPI production URL, persistent PostgreSQL, durable document storage or production secrets were available to configure.
- [ ] The existing GitHub Pages URL remains the legacy static app. It does not execute the Next.js + FastAPI application.
- [ ] Next release gate: provision the web/API hosting and durable services, configure environment variables and secrets, run migrations, then complete end-to-end upload → extract → index → retrieve → obligation SME review → graph exploration smoke tests.
- [ ] Address the 12 npm audit findings reported by CI (7 moderate, 4 high, 1 critical) before calling this production-ready.


### Intelligent RAG engine migration audit — 2026-11-20
- [x] Confirmed the MARAS Regulatory Intelligence API uses the modular `app.regulatory_rag.orchestrator.execute_regulatory_query` path for `POST /api/v1/regulatory-intelligence/query`.
- [x] Confirmed the orchestrator calls `retrieve_hybrid` from `app.regulatory_rag.engine`; the retrieval engine combines BM25 lexical ranking, optional Vertex AI embeddings/Firestore vector search, candidate graph expansion and reciprocal-rank fusion.
- [x] Confirmed the current MARAS index operation calls `index_document`, which persists chunks, candidate entities, edges and term frequencies in the local SQLite index; optional cloud mode also writes vectors and graph records to Firestore.
- [ ] Do not claim a complete production Agentic Graph RAG replacement yet. The engine is a modular hybrid RAG foundation, not a fully production-hardened agentic Graph RAG system.
- [ ] Default configuration has `rag_enabled = false`. Without explicit cloud configuration and the optional `rag` dependencies, query retrieval is primarily BM25 plus local candidate-graph expansion; Vertex/Firestore vector retrieval is not active.
- [ ] The current graph extractor in `app/regulatory_rag/graph.py` uses a small set of regex patterns for regulations, controls and processes. Its `MENTIONED_WITH` edges represent same-chunk co-mentions, not semantic/legal relationships. It does not yet provide ontology-backed relation extraction, entity resolution, confidence scoring, multi-hop reasoning or expert validation.
- [ ] The orchestrator's answer synthesis currently declares `NO_LLM_USED_EXTRACTIVE_ONLY`. It is not yet using a grounded generation model to synthesize answers with claim-level citations.
- [ ] The planner and orchestrator are bounded Python modules, not independent tool-using agents with durable state, retry policies, human approval gates and traceable tool execution. Agentic orchestration remains to be implemented.
- [ ] Current chunking/extraction path does not establish full-fidelity multimodal ingestion for scanned PDFs/OCR, tables, charts, figures, images and complex layouts. This must be validated and extended before marketing the product for arbitrary large multimodal regulatory corpora.
- [ ] Current cloud vector store writes to Firestore and uses vector search, but deployment requires configured Google Cloud project, model, Firestore vector index/database, credentials, dependency extras and explicit operational testing.
- [ ] Review the legacy document retrieval/extraction routes and migrate every product-facing retrieval consumer to the single Regulatory Intelligence engine. Keep MARAS source-of-truth, obligation review, requirements mapping and audit persistence as existing business capabilities; replace retrieval internals, not those business workflows.
- [ ] Add parity and regression tests proving every document Q&A, obligation extraction evidence lookup and graph exploration call uses the new engine and preserves source version/hash, page/section citation and access controls.

### Hosting decision and deployment gate — 2026-11-20
- [x] Confirmed the repository is a monorepo: Next.js frontend under `apps/web`, FastAPI backend under `apps/api`.
- [x] Confirmed Vercel can host the Next.js frontend, but deploying only `apps/web` does not deploy the FastAPI backend or provide durable storage for regulatory source files and the local SQLite RAG index.
- [ ] No deployment should be advertised as production-live until a backend host, managed PostgreSQL, durable object storage, API secrets and provider credentials are configured.
- [ ] Free-tier hosting can be used for a sponsor/demo environment, but verify free-tier sleep, compute, storage, request and data-retention limits. Do not upload confidential or regulated documents to an unapproved demo environment.
- [ ] Current GitHub Actions reports 12 npm audit findings (7 moderate, 4 high, 1 critical). Resolve or explicitly risk-accept with documented justification before a production release.
- [ ] Deployment still requires a reachable API, database migrations, durable document store, RAG provider configuration, end-to-end smoke tests and backup/restore checks.


## Intelligent RAG migration rollout — 2026-11-20

### Step 1 — unify MARAS retrieval entry points
- [x] Created isolated branch `feat/unified-intelligent-rag-rollout` from the latest `main`.
- [x] Routed the legacy Regulatory Intelligence evidence retrieval service through the existing `execute_regulatory_query` orchestrator rather than calling `retrieve_hybrid` directly.
- [x] The existing orchestrator now handles both the legacy `POST /retrieve` compatibility endpoint and the richer `POST /query` endpoint. Existing request/response compatibility is preserved for the retrieval endpoint; the query endpoint continues to expose planner, trace and generation status.
- [x] Kept existing MARAS business functions, source verification, document version/hash checks, obligation review, evidence approval and audit records intact.
- [x] No duplicate document store, obligations store or regulatory-source truth model introduced.
- [ ] CI and regression suite for this branch must pass before merge.
- [ ] Audit every remaining retrieval consumer and confirm none bypasses the orchestrator.
- [ ] After merge, inspect the deployed/runtime config separately; this code change does not activate Vertex/Firestore automatically.

### Step 1 technical boundaries
- Local mode remains the no-cost default: SQLite BM25 + candidate graph expansion.
- Vertex AI embeddings and Firestore vector/graph persistence remain opt-in behind `RAG_ENABLED` and cloud credentials.
- Existing graph relations are still heuristic `MENTIONED_WITH` co-occurrences. They must not be described as validated semantic/legal relations.
- Query generation remains extractive and source-verification gated; no ungrounded LLM generation has been introduced.
- This is the first migration step, not the completion of production Agentic Graph RAG.


## Stage 2 — structure-aware document extraction foundation — 2026-11-20

### Implemented on `feat/multimodal-ingestion-foundation`
- [x] Preserve DOCX table rows and cells in the existing controlled-document paragraph stream using explicit `[EXTRACTED TABLE n]` markers.
- [x] Detect and serialize PDF tables into the corresponding page text while preserving page-level source identity.
- [x] Attempt OCR for PDF pages with no selectable text using PyMuPDF's Tesseract OCR bridge.
- [x] Explicitly return `OCR_REQUIRED` when a PDF has no selectable text and OCR is unavailable or yields no text. This prevents scanned documents from being incorrectly marked as fully extracted and indexed as empty content.
- [x] Record OCR warnings, whether OCR was used, and table-preservation indicators in the existing extraction audit event.
- [x] Add regression coverage for DOCX table extraction and the scanned-PDF/OCR-unavailable path.
- [ ] CI verification and merge to main.
- [ ] Verify OCR success on an actual scanned regulatory PDF in a runtime with Tesseract installed.
- [ ] Add embedded image/figure extraction, OCR for image regions on mixed-content pages, chart/diagram interpretation, and richer layout metadata.
- [ ] Validate PDF table extraction against multi-page, merged-cell and complex-layout regulatory tables.

### Scope and limitations
- The original uploaded file remains unchanged; extracted table text is added to the existing extracted text stream.
- PDF OCR is currently an optional runtime capability. The Python package alone does not install the Tesseract system executable or language packs.
- This stage does not yet provide image captioning, chart understanding, figure relationship extraction or visual-layout reconstruction.
- No new document repository or parallel ingestion database was introduced. Existing MARAS document records, versioning, hashes, storage and audit events remain the source of truth.


---

# MARAS + Intelligent Agentic Graph RAG — Living Delivery Register

> This file is the operational source of truth for implementation status. A checkbox is not considered complete merely because code exists. Every `[x]` must have a verification method and evidence (test, CI run, API result, deployment URL or reviewer sign-off). Use `[~]` for partial, `[ ]` for not started, and `[!]` for failed or blocked. Never silently convert a failed or unverified item to complete.

## A. Product outcome and architecture contract

- [ ] One MARAS application with existing regulatory source-of-truth, document versioning, obligation review, approvals and audit workflows retained.
- [ ] One production-grade intelligent RAG retrieval contract used by every product-facing retrieval consumer.
- [ ] Multimodal ingestion preserves provenance for text, tables, images, diagrams, charts and OCR content.
- [ ] Graph entities and relations are semantically grounded, versioned, confidence-scored and traceable to source spans.
- [ ] Agent orchestration is bounded, observable, retry-safe, permission-aware and supports human approval where actions affect regulatory decisions.
- [ ] Every generated answer and obligation recommendation is evidence-grounded with claim-level source citations.
- [ ] Reproducible evaluation, security, operational monitoring, deployment and recovery are in place.

## B. Status vocabulary and evidence rules

| Status | Meaning | Completion evidence |
|---|---|---|
| `[ ]` Not started | No implementation yet | None |
| `[~]` Partial | Some code exists; acceptance criteria remain | List completed and missing criteria |
| `[x]` Verified | All acceptance criteria passed | Test/CI/API/deployment evidence |
| `[!]` Failed/blocked | Verification failed or external dependency blocks work | Failure log and remediation owner/action |

Rules:
1. Record exact repository path(s), PR, commit SHA and CI run for every code change.
2. Record the exact test command and result. A passing lint is not a passing functional test.
3. For API work, record request, expected response, actual response and authorization/provenance checks.
4. For UI work, record browser/device, workflow, screenshots or reproducible steps.
5. For external services, distinguish code support from provisioned/configured/live service.
6. Do not mark production-ready until deployment, security, data durability, backup/restore and end-to-end smoke tests pass.
7. When a check fails, keep it visible under Failed/Blocked until fixed and re-run successfully.
8. After merge, reconcile this register against `main`; do not rely on feature-branch-only checkboxes.

## C. Implementation and verification register

### C1. Existing MARAS product capabilities (baseline audit)

| Capability | Implementation evidence to locate | Verification checklist | Status |
|---|---|---|---|
| Regulatory document records and versioning | Existing document models/services | Upload two versions; confirm immutable file hash/version and correct current version | [~] |
| Source document storage | Existing storage adapter/config | Restart service; verify file still exists and hash matches | [~] |
| Obligation extraction and review | Existing obligation routes/services/UI | Extract, edit, approve/reject; verify audit history and source links | [~] |
| Requirements mapping | Existing mapping routes/services | Map requirement to evidence; verify provenance and permissions | [~] |
| Audit events | Existing audit service/models | Exercise upload, extraction, review and approval; verify actor/time/action | [~] |
| Graph explorer UI | `apps/web/components/regulatory-graph-explorer.tsx` | Load graph for a current document; test empty, stale, unauthorized and valid cases | [~] |
| Authenticated graph API | `apps/api/app/api/v1/regulatory_intelligence.py` | Verify auth, document ownership/access, current version and file hash | [~] |

Baseline status is partial until each verification is executed and recorded. Existing presence in source code is not proof of working end-to-end behaviour.

### C2. Intelligent RAG migration

| Work item | Implementation evidence | Verification checklist | Status |
|---|---|---|---|
| Unified retrieval orchestrator | `apps/api/app/regulatory_rag/orchestrator.py`; `apps/api/app/services/regulatory_intelligence.py` | Verify all public retrieval paths use the same orchestrator; test API contract parity | [~] |
| Lexical/BM25 retrieval | `apps/api/app/regulatory_rag/engine.py` | Query exact terms, synonyms and no-match terms; measure recall/precision on labelled set | [~] |
| Vector retrieval | Vertex/Firestore adapter and configuration | Enable with real credentials/index; verify vector writes, reads, filtering and fallback | [ ] |
| Hybrid fusion | RRF in retrieval engine | Compare lexical-only, vector-only and fused ranking on fixed evaluation queries | [~] |
| Graph expansion | Candidate graph in retrieval engine | Verify graph expansion is document/version scoped and cannot cross tenant boundaries | [~] |
| Semantic graph extraction | Current `apps/api/app/regulatory_rag/graph.py` | Replace co-mention-only edges with typed relations, source spans, confidence and validation | [ ] |
| Entity resolution | Not yet established | Test aliases, duplicate entities, jurisdiction collisions and conflicting definitions | [ ] |
| Multi-hop reasoning | Not yet established | Test multi-document and multi-hop questions with path-level evidence citations | [ ] |
| Grounded generation | Current synthesis is extractive (`NO_LLM_USED_EXTRACTIVE_ONLY`) | Verify each generated claim is supported by citations; reject unsupported claims | [ ] |
| Retrieval evaluation | Evaluation harness/dataset to be established | Track Recall@k, MRR/nDCG, answer faithfulness, citation precision/recall and latency | [ ] |
| Tenant/access isolation | Existing auth and document filters | Attempt cross-tenant and unauthorized retrieval; expect deny/no leakage | [ ] |

### C3. Multimodal ingestion

| Work item | Implementation evidence | Verification checklist | Status |
|---|---|---|---|
| PDF selectable text | `apps/api/app/services/document_extraction.py` | Extract text from multi-page PDF; verify page-level ordering and provenance | [~] |
| PDF table detection | Same file, `find_tables()` | Test simple, multi-page, merged-cell and complex tables against expected cells | [~] |
| DOCX paragraphs | Same file | Verify paragraph order and text | [~] |
| DOCX tables | Same file, `[EXTRACTED TABLE n]` | Test headers, rows, merged cells and nested tables; verify no cell loss | [~] |
| Scanned PDF OCR | PyMuPDF Tesseract bridge | Test OCR success with installed Tesseract + language pack; test OCR missing/failure | [~] |
| Mixed pages (text + embedded images) | Not yet established | Verify image regions are extracted/OCR'd without dropping selectable text | [ ] |
| Image attachments | Not yet established | Test PNG/JPEG/TIFF input, orientation, resolution and OCR confidence | [ ] |
| Charts/diagrams/figures | Not yet established | Test visual interpretation, labels, legends, relationships and evidence coordinates | [ ] |
| Layout and reading order | Not yet established | Test columns, headers/footers, footnotes, tables and multi-column pages | [ ] |
| Large files and async processing | Not yet established | Load test file-size limits, worker queues, retries, cancellation and idempotency | [ ] |
| Extraction failure handling | `OCR_REQUIRED` / `EXTRACTION_FAILED` | Ensure failed/partial extraction cannot be silently indexed as complete | [~] |

### C4. Agentic workflow and controls

- [ ] Define agent responsibilities, tools, input/output schemas and least-privilege permissions.
- [ ] Implement planner → retrieval → graph reasoning → evidence validation → synthesis flow.
- [ ] Add bounded step/time/token budgets, retries, timeouts and idempotency.
- [ ] Persist run state, intermediate evidence, tool calls and failure reasons.
- [ ] Add human-in-the-loop approval before regulatory decisions or external side effects.
- [ ] Add prompt-injection and malicious-document handling; treat ingested content as untrusted data.
- [ ] Add deterministic replay and regression tests for agent traces.
- [ ] Add agent evaluation for tool selection, groundedness, completeness and refusal behaviour.

### C5. API, UI and workflow integration

- [ ] Inventory every retrieval call site across API routes, services, background jobs and UI proxy routes.
- [ ] Prove document Q&A uses the unified RAG orchestrator.
- [ ] Prove obligation extraction/evidence lookup uses the unified RAG orchestrator.
- [ ] Prove requirements mapping/evidence lookup uses the unified RAG orchestrator.
- [ ] Prove graph exploration reads the current graph index and respects source version/hash.
- [ ] Preserve existing MARAS business workflow and API compatibility where required.
- [ ] Add end-to-end test: upload → parse → index → query → obligation review → approve/reject → audit → graph.
- [ ] Verify error, empty, stale-index, unsupported-file and unauthorized states in UI.

### C6. Security, reliability and performance

- [ ] Resolve or document risk acceptance for all dependency vulnerabilities; current recorded baseline: 12 npm audit findings (7 moderate, 4 high, 1 critical).
- [ ] Add malware/file-type/size validation and safe parser limits.
- [ ] Verify secrets are environment-managed and never committed/logged.
- [ ] Verify tenant isolation, RBAC and document-level authorization across all retrieval paths.
- [ ] Verify encryption in transit and at rest for stored source documents and indexes.
- [ ] Add structured logs, traces, metrics, alerting and correlation IDs.
- [ ] Load test large regulatory corpora, concurrent ingestion and retrieval latency.
- [ ] Verify backup/restore, retention, deletion and re-indexing procedures.
- [ ] Verify graceful degradation when embedding provider, vector DB or LLM is unavailable.

### C7. Deployment and release

- [ ] Choose and document frontend, API, database, object storage and vector/graph hosting.
- [ ] Configure staging and demo environments without using confidential regulatory documents.
- [ ] Provision persistent database and durable document storage; do not rely on ephemeral filesystem/local SQLite in hosted production.
- [ ] Configure environment variables, secrets, CORS, auth callbacks and provider credentials.
- [ ] Run database migrations and verify rollback procedure.
- [ ] Deploy frontend and API; record exact public URLs and commit SHA.
- [ ] Run health/readiness checks and end-to-end smoke test against deployed services.
- [ ] Verify restart/redeploy does not lose documents, indexes or audit records.
- [ ] Verify backups and restore into a clean environment.
- [ ] Record release approval and known limitations.

## D. Current verified delivery history

| PR / commit | Change | CI / merge state |
|---|---|---|
| PR #48 | Route legacy Regulatory Intelligence retrieval through unified orchestrator | Merged to main; CI passed |
| Main `6271369a167f` | Unified retrieval migration | Main sync confirmed |
| PR #49 | PDF/DOCX table extraction and OCR fallback foundation | Open; initial CI failed on Ruff E501; lint fix committed on feature branch; re-run required |

### PR #49 failure and remediation
- [x] Failure identified from CI run `44760117497`: Ruff E501 line length in `apps/api/app/services/document_ingestion.py`.
- [x] Remediation committed: `6a72c07d989541599d9e8ffdcbe4c3a8fba7961f`.
- [ ] Re-run PR #49 CI and confirm all verification gates pass.
- [ ] Review functional test output, not just lint.
- [ ] Merge only after green CI; then verify merge SHA and main branch CI.

## E. Mandatory execution handoff format

Every future implementation session must update this block:

**Current stage:** PR #49 multimodal extraction foundation  
**Current branch:** `feat/multimodal-ingestion-foundation`  
**Current PR:** https://github.com/usp1904/Regulatory-AugSys/pull/49  
**Last known blocker:** Ruff E501; fix committed, CI rerun pending  
**Next action:** Inspect latest PR checks; fix all failures; merge only after green checks  
**Next stage after merge:** Complete OCR runtime verification, then mixed-page image/figure extraction  
**Main branch SHA:** `6271369a167f9d07306a4224c6b6e0a831e79b40` (last verified before PR #49 merge)

Before starting new work:
1. Fetch latest `main`, PR state, latest branch SHA and CI results.
2. Read this register and inspect the exact source files for the current stage.
3. Reconcile documented status with actual code and test evidence.
4. Resume the first incomplete or failed checklist item; do not redo verified work.
5. Update this file in the same PR as the implementation.
6. After merge, verify main SHA and main CI, then update the handoff block.

## F. Known non-goals until explicitly approved
- Do not create a second MARAS source-of-truth, document store, obligation store or audit system.
- Do not label heuristic co-mention graph edges as legally validated relationships.
- Do not label extractive retrieval as LLM-grounded generation.
- Do not label local SQLite or optional cloud adapters as production infrastructure without operational verification.
- Do not call the product production-live before the deployment checklist is complete.


## Stage 2 merge reconciliation — 2026-11-20

- [x] PR #49 merged to `main` after both latest PR CI runs passed.
- PR: https://github.com/usp1904/Regulatory-AugSys/pull/49
- PR head SHA verified before merge: `029874edc62046987c5d39c759988fccbe8cf3fd`.
- Merge commit / new main SHA: `47f40d62b7595bb3c472efc7716a266a1387b11b`.
- PR CI run `44761537253` for the final PR head: completed successfully.
- PR CI run `44761454656` for the lint-fix commit: completed successfully.
- Earlier CI run `44760117497` failed on Ruff E501 and was superseded by the successful runs above.
- [ ] Verify a new CI run triggered for the merge commit on `main`; no run associated with the merge SHA was visible at reconciliation time.
- [ ] Verify OCR success against a real scanned regulatory PDF in a runtime with Tesseract and language data installed.
- [ ] Continue with mixed-page embedded-image OCR, figure/chart/diagram extraction and layout/provenance validation.

**Current stage:** PR #49 merged; main-branch integration validation pending.  
**Current branch:** `main`  
**Current PR:** https://github.com/usp1904/Regulatory-AugSys/pull/49 (merged)  
**Next action:** Verify main CI and application behaviour on the merged code, then test OCR runtime with a scanned PDF.  
**Main branch SHA:** `47f40d62b7595bb3c472efc7716a266a1387b11b`


## UI visibility and Global Compare regression audit — 2026-11-20

### Verified findings
- The public GitHub Pages deployment is the legacy single-file app served from repository-root `index.html`; the new Next.js + FastAPI workspace under `apps/web` and `apps/api` is a separate application and is not made live by merging backend changes alone.
- The Next.js app has an Intelligence route at `/regulatory-intelligence` and a navigation entry labelled `Intelligence` in `apps/web/components/site-shell.tsx`. It does not have a dedicated Agentic RAG tab/workspace yet.
- PR #49 changed only `a.md`, `apps/api/app/services/document_extraction.py`, `apps/api/app/services/document_ingestion.py` and `apps/api/tests/test_document_ingestion.py`; it made no frontend changes.
- The legacy `index.html` still contains the Global Compare tab and comparison engine. Its cross-market matrix section and graph are marked `maras-internal-only`. The default end-user surface hides all `.maras-internal-only` content; `?internal=1` opts into the internal surface. This explains why the tab can remain visible while its matrix and advanced controls are hidden.
- The Global Compare visibility restriction predates PR #49. The current `index.html` content is identical to its parent version before the 2026-11-20 workspace commits; PR #49 did not remove Global Compare code.
- The Next.js application has no Global Compare route or navigation entry. The legacy workflow note exists at `docs/workflows/notion-export/wf-global-compare.md`, but that document is not a working UI.

### Corrective work required (not yet implemented)
- [ ] Decide and implement the supported product surface: either deploy the Next.js app as the main user-facing app or continue the static app and integrate the RAG experience there. Do not assume GitHub Pages can host FastAPI.
- [ ] Add a clearly labelled RAG workspace/tab with document selection, extraction status, indexing, retrieval, evidence, and execution trace; connect it to the deployed API.
- [ ] Restore the Global Compare matrix, market filters, gap analysis and comparison outputs to the intended user surface, while retaining only genuinely staff-only diagnostics behind the internal flag.
- [ ] Add UI regression tests proving Global Compare matrix and controls are visible in default mode and functional in internal mode.
- [ ] Add end-to-end validation for upload → extraction → index → query → cited evidence using the same deployed frontend/API.
- [ ] Re-run CI and deployment smoke tests after UI changes.

**Current UI integration status:** Not delivered. PR #49 was backend-only.  
**Global Compare status:** Code remains in legacy `index.html`; its matrix/graph are hidden in default end-user mode by `maras-internal-only`.  
**Do not mark UI validation complete until the actual deployed URL exposes and passes these workflows.**


## Intelligent RAG workspace UI implementation — 2026-11-20

- [~] Added an `Intelligent RAG` tab and functional workspace to the GitHub Pages application in root `index.html`.
- [x] Workspace UI includes API connection/health check, document upload and listing, extraction status, document indexing, candidate graph inspection, query execution, retrieval plan, execution trace and evidence provenance.
- [x] Workspace uses existing API contracts:
  - `GET /health`
  - `GET /api/v1/documents`
  - `POST /api/v1/documents`
  - `POST /api/v1/regulatory-intelligence/index`
  - `GET /api/v1/regulatory-intelligence/graph/{document_id}`
  - `POST /api/v1/regulatory-intelligence/query`
- [x] API base URL and access key are held in browser session storage only; key is not embedded in source.
- [x] API CORS is configurable through `CORS_ALLOWED_ORIGINS` (default includes `https://usp1904.github.io` and local Next.js origins).
- [x] Restored Global Compare's graph, matrix, and cross-market matrix section to the default user surface; no longer hidden behind `maras-internal-only`.
- [x] UI explicitly discloses current extraction limitations and `NO_LLM_USED_EXTRACTIVE_ONLY`; graph is labelled candidate co-mention, not validated regulatory relationships.
- [ ] Run frontend lint/build and backend tests; fix any failures.
- [ ] Verify rendered tab and Global Compare in a browser against GitHub Pages.
- [ ] Deploy FastAPI backend with persistent storage/database, HTTPS, secrets, configured CORS and authentication; this is not provisioned by GitHub Pages.
- [ ] Validate end-to-end upload → extraction → index → query → cited evidence and graph against the deployed API.
- [ ] Merge to `main` only after checks pass, then confirm GitHub Pages deployment.

**Important integration dependency:** the GitHub Pages site is static. The RAG tab is now present in the frontend source but will show API unavailable until a reachable FastAPI backend is deployed and its base URL plus access key are configured. The current document endpoints are not uniformly protected by the same access-key dependencies as the regulatory-intelligence endpoints; deploy only behind an appropriate trusted access boundary and resolve endpoint authorization before exposing the API publicly.

**Current branch:** `feat/agentic-rag-workspace-ui`  
**Next action:** run CI and review frontend/backend checks before opening or merging the PR.
