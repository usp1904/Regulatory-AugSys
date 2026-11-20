# Zero-budget MARAS Regulatory Intelligence demo

This guide runs the current prototype locally. It does not require Vertex AI, Firestore, Neo4j, a paid LLM or a hosted database.

## 1. Start the existing MARAS application

From the repository root:

\`\`\`bash
cp .env.example .env
docker compose up --build
\`\`\`

In a second terminal, apply the existing database migrations:

\`\`\`bash
docker compose exec api alembic upgrade head
\`\`\`

Open:
- MARAS web application: http://localhost:3000
- Regulatory Intelligence workspace: http://localhost:3000/regulatory-intelligence
- API health: http://localhost:8000/health

If not using Docker, follow the existing local API and web setup in the root README. Use Python 3.12+ and Node 22+.

## 2. Ingest an approved source document

Use the existing MARAS Documents workflow to upload a PDF, DOCX or TXT. Wait for extraction to complete. Do not upload confidential or restricted documents to a public demo environment.

For the current local parser, scanned PDFs without an embedded text layer are not OCR-processed. Use a text-searchable PDF for this first demo.

## 3. Register and verify source authority

The source-truth workflow already exists in MARAS. It is exposed through the Requirements Mapping API and is reused by the RAG engine.

Create the source record. Replace the example values with the actual official publication metadata and the document ID returned by MARAS:

\`\`\`bash
curl -X POST http://localhost:8000/api/v1/requirements-mappings/regulatory-sources \\
  -H "Authorization: Bearer $MARAS_REQUIREMENTS_MAPPING_WRITE_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "document_id": 1,
    "title": "Official regulation title",
    "issuing_authority": "Issuing authority",
    "jurisdiction": "Jurisdiction",
    "document_type": "Regulation",
    "official_url": "https://official-authority.example/regulation",
    "version_label": "Published version",
    "publication_date": null,
    "effective_date": null,
    "applicability_scope": "Describe the scope and intended regulated activities.",
    "created_by": "Local demo operator"
  }'
\`\`\`

The response contains the new source record \`id\`. Review the official URL, issuer, jurisdiction, version and SHA-256 against the actual source. Only then mark it VERIFIED:

\`\`\`bash
curl -X PUT http://localhost:8000/api/v1/requirements-mappings/regulatory-sources/SOURCE_ID/review \\
  -H "Authorization: Bearer $MARAS_REQUIREMENTS_MAPPING_REVIEW_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "reviewer": "Independent source reviewer",
    "decision": "VERIFIED",
    "rationale": "Official publication and current document hash were checked."
  }'
\`\`\`

Do not mark a source VERIFIED merely to make the demo produce an answer. The review is a real source-authority gate.

## 4. Build the local index

Open http://localhost:3000/regulatory-intelligence.

1. Refresh the document list.
2. Select the extracted source document.
3. Click **Build / refresh RAG index**.
4. Confirm chunk, entity and candidate-edge counts.
5. The index is stored under \`STORAGE_ROOT/indexes/regulatory_rag.sqlite3\`.

The local index is derived data. MARAS document records and the original file remain authoritative.

## 5. Ask a question and inspect evidence

Try a narrow question that uses the actual document's terminology, for example:

\`\`\`text
Which audit trail controls are required by the selected regulation?
\`\`\`

Inspect:
- Query intent and retrieval strategy.
- BM25 and graph retrieval trace.
- Exact source excerpt.
- Document ID, version, SHA-256 and page/chunk location.
- MARAS source status.

Only a source record marked VERIFIED with a matching content hash can produce the extractive evidence synthesis. UNREGISTERED, UNVERIFIED, REJECTED or STALE sources can still be inspected as retrieved passages, but the synthesis layer abstains.

## 6. What this demo proves

- Existing MARAS documents can be indexed without duplicating document storage.
- A persistent local BM25 and candidate-graph index can be built with no cloud dependency.
- Retrieval is constrained to selected documents and current source versions.
- Every returned passage has a stable source reference.
- Source verification and content-hash checks gate evidence synthesis.
- Displayed synthesis statements are verbatim source sentences, not generated regulatory interpretations.

## 7. Known prototype limits

- PDF, DOCX and TXT extraction only; no scanned-PDF OCR, tables, charts, PPTX, XLSX, EPUB or audio/video pipeline yet.
- BM25 is lexical retrieval, not dense semantic search.
- Graph edges are co-mentions, not validated legal relationships.
- Indexing runs synchronously.
- No autonomous LLM agent execution or regulatory advice generation.
- Local deployment is for controlled demonstration, not multi-tenant production.

## 8. Sponsor demonstration

Use one public, official, text-searchable regulation and a small set of focused questions. Demonstrate source verification, indexing, evidence retrieval, citations and abstention. Do not claim regulatory correctness from retrieval metrics alone. The next sponsor-funded milestones should be multimodal OCR/layout extraction, local dense embeddings after hardware evaluation, durable indexing jobs, validated regulatory relationships, SME evaluation and production security.
