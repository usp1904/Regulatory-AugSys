# MARAS Agentic Graph RAG — Build Sequence and Delivery Status

**Repository:** `usp1904/Regulatory-AugSys`  
**Implementation branch:** `feature/maras-agentic-graph-rag`  
**Baseline:** `main`  
**Plan owner:** Product / Engineering  
**Last updated:** 2026-11-20  
**Status:** In progress. Initial evidence-retrieval vertical slice is being added. This is not yet a production Graph RAG deployment.

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
- Google Vertex AI for model and embedding access, subject to project credentials and model availability.
- Firebase/Firestore is the preferred first vector-store direction to validate.
- Do not introduce Neo4j for the MVP.
- A Firestore entity/edge model is not a native graph database. Benchmark bounded adjacency traversal and query scale. Keep graph storage behind an interface so a dedicated graph store can be introduced later without changing MARAS workflows.
- OCR may use Google Document AI, subject to credentials, regional availability, data residency, and cost approval.
- Evaluate Docling for structure-aware parsing; do not add it until the deployment image and representative regulatory documents pass tests.
- Begin with an explicit Python state machine and typed tool contracts. Add a framework only if it solves a demonstrated orchestration need.
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

**Scope warning:** This first slice is lexical evidence retrieval, not embeddings, graph traversal, agentic reasoning or generated regulatory advice. It is a safe foundation and UI/API integration check.

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

### New files added in Phase 1
- `apps/api/app/schemas/regulatory_intelligence.py`
- `apps/api/app/services/regulatory_intelligence.py`
- `apps/api/app/api/v1/regulatory_intelligence.py`
- `apps/api/tests/test_regulatory_intelligence.py`
- `apps/web/app/regulatory-intelligence/page.tsx`
- `apps/web/components/regulatory-intelligence-workbench.tsx`
- `apps/web/app/api/regulatory-intelligence/retrieve/route.ts`

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

Initial retrieval endpoint:
- `POST /api/v1/regulatory-intelligence/retrieve`
- Request: query, optional document IDs, top-K.
- Response: status, query, evidence list and scope message.
- Access: existing MARAS mapping-reader credentials for this initial internal workspace.
- Frontend: server-side Next.js proxy. Never send the service key to browser JavaScript.

Planned future endpoints:
- `POST /api/v1/regulatory-intelligence/query`
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
| Regulatory Intelligence UI | In progress | Phase 1 |
| Source-grounded retrieval API | In progress | Phase 1 |
| Automated tests | Not verified | Run backend and frontend suites |
| Persistent indexing | Not started | Phase 2 |
| Multimodal parsing/OCR | Not started | Phase 2 |
| Persistent knowledge graph | Not started | Phase 3 |
| Vector embeddings | Not started | Phase 4 |
| Agent orchestration | Not started | Phase 5 |
| Production security/observability | Not started | Phase 7 |
| Deployment | Not started | Credentials and target environment required |

### Current honest product maturity

**Phase 1 prototype / internal integration slice.** Not a production Agentic Graph RAG system. Do not market it as such until Phases 2–7 are implemented, evaluated and deployed.

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
