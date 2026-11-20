# MARAS Regulatory Intelligence Engine

This document describes the current implementation in the `apps/api/app/regulatory_rag/` package and the steps required to enable cloud-backed retrieval.

## Current request flow

1. MARAS stores the authoritative source file and its extracted `Document`, `DocumentPage`, `DocumentParagraph` records.
2. The Regulatory Intelligence workspace lists extracted documents through `GET /api/v1/regulatory-intelligence/documents`.
3. An authorized writer requests indexing through `POST /api/v1/regulatory-intelligence/index`.
4. The chunker creates stable chunks tied to document ID, version, SHA-256 and page/paragraph ordinal.
5. The graph extractor proposes candidate entities for regulatory references, controls and processes. Edges are `MENTIONED_WITH` co-occurrence facts and always retain a chunk ID and excerpt.
6. With cloud mode disabled, retrieval ranks source chunks lexically and expands matching candidate graph facts in-process.
7. With cloud mode enabled, Vertex AI embeddings are persisted as Firestore vector fields. Firestore vector search is fused with lexical results using reciprocal-rank fusion. Persistent graph edges can add a bounded relevance boost.
8. All returned passages retain source document ID, version, SHA-256 and page/chunk location.

## Install optional cloud dependencies

From `apps/api`:

```bash
pip install -e ".[dev,rag]"
```

## Environment configuration

Set these variables in the API runtime, not in browser code:

```dotenv
RAG_ENABLED=true
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
FIRESTORE_DATABASE=(default)
RAG_COLLECTION_PREFIX=maras_rag
RAG_EMBEDDING_MODEL=text-embedding-005
RAG_EMBEDDING_DIMENSIONS=768
```

Use Application Default Credentials or the deployment platform's workload identity. Do not commit service-account keys. Grant only the required Vertex AI prediction and Firestore database permissions.

## Firestore vector index prerequisite

Create a vector index on the `embedding` field in collection `maras_rag_chunks` with the configured embedding dimensions and cosine distance. Firestore requires a vector index for nearest-neighbour queries. Confirm that the selected database, region, project and SDK version support vector search before enabling `RAG_ENABLED`.

## Important limitations

- The current API index operation runs synchronously. It is suitable for a small internal pilot, not large document libraries. A durable queue and worker are required before production.
- The current MARAS extractor supports PDF, DOCX and TXT. OCR, image/table/chart extraction, PPTX, XLSX, EPUB and audio/video processing are not implemented by this engine yet.
- Candidate graph relations are deterministic co-mentions, not verified legal relationships. SME validation and richer relation extraction are required.
- Current local graph expansion is computed from the selected documents at query time. Persistent graph edges are written only when cloud indexing is enabled.
- Current access reuses MARAS requirements-mapping reader/writer keys. Tenant-level and document-level authorization must be added before multi-tenant use.
- No answer-generation endpoint is enabled yet. The engine returns evidence passages only. A grounded generation layer must validate every claim against evidence before displaying regulatory interpretations.
- Firestore vector index, GCP credentials, quotas, billing, retention, deletion propagation, observability and regional data-residency controls are deployment prerequisites.
- Retrieval ranking scores are not calibrated confidence and must not be interpreted as regulatory certainty.

## API endpoints

- `GET /api/v1/regulatory-intelligence/documents`: list extracted MARAS sources.
- `POST /api/v1/regulatory-intelligence/index`: index one source document; writer authorization required.
- `POST /api/v1/regulatory-intelligence/retrieve`: retrieve grounded evidence; reader authorization required.

## Next engineering increments

1. Durable indexing jobs with status, retries, idempotency and deletion propagation.
2. Layout-aware parser and OCR adapters with page coordinates and table/figure extraction.
3. More precise regulatory entity and relation schema with evidence-backed edge validation.
4. Persistent index manifest, pipeline versioning and index freshness checks.
5. Intent classifier, query planner, reranker and bounded agent orchestration.
6. Claim-to-evidence validation, source-authority checks, contradiction detection and abstention.
7. Integration with the existing obligation review, requirements mapping, clarification and evidence workflows.
8. SME-labelled retrieval/generation evaluation suite, tenant isolation and production observability.
