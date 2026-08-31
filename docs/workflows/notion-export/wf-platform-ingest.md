# Controlled document ingestion

**Workflow ID:** WF-PLATFORM-INGEST
**Graph:** Upload → Hash → Parse → Store → Audit

## MVP traceability

- MVP-22
- MVP-23

## API

- `POST /api/v1/documents`
- `GET /api/v1/documents/{id}`

## Web routes

- `/documents/{id}`

## Verification

- `apps/api/tests/test_document_ingestion.py`
- `pytest`
