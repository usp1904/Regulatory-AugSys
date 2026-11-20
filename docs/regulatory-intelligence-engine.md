# MARAS Regulatory Intelligence Engine

The engine adds a zero-budget local retrieval path inside the existing MARAS application. It reuses MARAS document records and does not create a second document repository.

## Local request flow

1. MARAS stores the authoritative source file and extracted `Document`, `DocumentPage`, and `DocumentParagraph` records.
2. The Regulatory Intelligence workspace lists extracted documents through `GET /api/v1/regulatory-intelligence/documents`.
3. An authorized writer requests indexing through `POST /api/v1/regulatory-intelligence/index`.
4. The chunker creates stable chunks tied to document ID, version, SHA-256 and page/paragraph ordinal.
5. The graph extractor proposes candidate entities and `MENTIONED_WITH` edges. Each edge retains its source chunk and excerpt.
6. The local index stores chunks, term-frequency data, entities and edges in SQLite under `STORAGE_ROOT/indexes/regulatory_rag.sqlite3`. The index is derived data; MARAS PostgreSQL/SQLite business records remain authoritative.
7. Queries use BM25 ranking and bounded graph expansion. Results are filtered against the current document version and SHA-256 before they are returned.
8. The orchestrator returns the query plan, execution trace and evidence passages.

## Zero-budget runtime

No additional Python package is required for the local path. It uses:
- Python standard-library SQLite for persistence.
- Dependency-free BM25 implementation.
- Existing SQLAlchemy document models and extraction services.
- Existing deterministic candidate graph extraction.

Run the existing API setup:

```bash
cd apps/api
pip install -e ".[dev]"
```

The default `RAG_ENABLED=false` setting disables optional cloud providers, not local indexing. The local SQLite index is created automatically under the configured `STORAGE_ROOT` when a document is indexed. The repository's `.gitignore` excludes local storage.

## Optional future cloud adapter

Vertex AI and Firestore adapters remain optional. They are not required to build or demonstrate the local MVP. If a sponsor later funds hosted embeddings or vector search, install:

```bash
pip install -e ".[dev,rag]"
```

Then configure server-side GCP project, location, Firestore database, Vertex embedding model, IAM and a Firestore vector index. Do not commit service-account keys.

## Current limitations

- The local retrieval path uses BM25, not dense semantic embeddings. Exact clause, terminology and keyword retrieval are supported; semantic paraphrase recall needs a local embedding model or a funded provider later.
- The current MARAS extractor supports PDF, DOCX and TXT. OCR, scanned-PDF processing, tables, figures, PPTX, XLSX, EPUB and audio/video extraction are not yet implemented.
- Graph edges are deterministic co-mentions, not verified legal relationships. They must not be represented as authoritative regulatory logic.
- Indexing is synchronous. It is suitable for small pilot corpora, not large-scale production ingestion.
- The current engine returns evidence, not generated regulatory advice. Claim-to-evidence validation, source-authority checks, contradiction handling and abstention are still required.
- Current access reuses MARAS requirements-mapping reader/writer credentials. Tenant-level and document-level authorization must be added before external multi-tenant use.
- Ranking scores are retrieval signals, not regulatory confidence.

## API endpoints

- `GET /api/v1/regulatory-intelligence/documents`: list extracted MARAS sources.
- `POST /api/v1/regulatory-intelligence/index`: build or refresh the local index for one source document.
- `POST /api/v1/regulatory-intelligence/query`: plan the query and return ranked evidence with an execution trace.
- `POST /api/v1/regulatory-intelligence/retrieve`: compatibility retrieval endpoint.

## Next engineering increments

1. Add index status and freshness indicators to the UI.
2. Add incremental re-indexing and robust stale-index cleanup.
3. Improve entity normalization and introduce evidence-backed relationship types.
4. Add local OCR and layout-aware table/figure extraction using available open-source tools.
5. Add a local embedding adapter only after model size, RAM/VRAM and latency are measured on the target machine.
6. Add claim-to-evidence validation, source-authority checks, contradiction detection and abstention.
7. Connect accepted candidates to existing MARAS obligation review and requirements mapping.
8. Add a labelled evaluation corpus and measure Recall@K, Precision@K, MRR, citation correctness and latency.
