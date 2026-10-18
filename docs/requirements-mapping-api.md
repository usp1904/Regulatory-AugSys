# Requirements Mapping API — persistent draft workflow

This slice adds persistent requirements-mapping records to the existing FastAPI + SQLAlchemy platform. It does not require a Firebase project; the current PostgreSQL/SQLite persistence layer is reused so the project can be configured later without creating a second data store.

## Endpoints

- `POST /api/v1/requirements-mappings` — create a draft mapping. The API does not accept client-side approval as authoritative; review starts as `PENDING`.
- `GET /api/v1/requirements-mappings?dossier_id=...` — list mappings, optionally scoped to a dossier.
- `GET /api/v1/requirements-mappings/{id}` — retrieve a mapping.
- `PUT /api/v1/requirements-mappings/{id}` — revise a mapping after stakeholder clarification; source evidence is revalidated and prior review is reset.
- `POST /api/v1/requirements-mappings/{id}/review` — record a reviewer decision. Approval is rejected with HTTP 409 while completeness blockers remain.
- Web UI: `/requirements-mappings` — select source documents, capture obligations and system impact, record decisions, draft PBIs, inspect blockers, and review mappings.

## Data and controls

- Mapping body is stored as JSON text, preserving the source, obligation, system finding/evidence, clarification, requirement, PBI, acceptance criteria, and test evidence fields.
- Mapping creation requires an existing controlled source document ID. The API checks the excerpt against the document's extracted text and copies the stored document ID, version, and SHA-256 into the mapping; client-supplied version/hash values are not trusted.
- Mapping records and review decisions produce audit events with actor, event type, and mapping key.
- Readiness is computed from the stored data on response; client-supplied readiness labels are not trusted.
- An unresolved interpretation, unfinalized applicability, unreviewed source, missing evidence, open dependency, missing test evidence, or incomplete PBI blocks approval.
- Routes require separate server-side writer and reviewer bearer keys. Set `MARAS_REQUIREMENTS_MAPPING_WRITE_KEY` and `MARAS_REQUIREMENTS_MAPPING_REVIEW_KEY` in the API environment; blank/unset keys fail closed with HTTP 503. Reviewer routes reject writer-only keys.
- These are shared service credentials, not individual identity. Reviewer name is still supplied by the request, so this is an interim access boundary—not user-level authentication or a validated electronic signature. Do not expose either key in browser JavaScript or public hosting.

## Database migration

Run from `apps/api`:

```bash
alembic upgrade head
```

The migration adds the `requirements_mappings` table and indexes. Test fixtures create tables from SQLAlchemy metadata in an isolated SQLite database.

## Test coverage

`tests/test_requirements_mapping.py` covers persistence, draft status, audit events, rejection of approval when the decision is unresolved, successful approval when all gates pass, dossier filtering, 404 handling, writer/reviewer key separation, and fail-closed missing-key configuration.

## Known production gaps

- Per-user authentication, managed identity, and fine-grained role-based authorization are not implemented; the current separate shared writer/reviewer keys are an interim server-to-server control.
- Reviewer identity is a supplied string, not an authenticated principal or electronic signature.
- Source URL/revision/hash and source approval fields are still user-entered attestations; there is no independent source acquisition or hash verification in this slice.
- There is no automatic AI clause extraction or direct Azure DevOps publishing yet.
- Do not use this as a validated GxP/Part 11 system or as evidence of legal compliance.

## Next sequence

1. Add authentication and role-based permissions, with audit actor identity derived from the authenticated principal.
2. Integrate the browser workbench with this API for local/deployed environments without embedding secrets in the browser.
3. Add controlled source ingestion, independent file hashing, parser and malware scanning gates.
4. Add versioned clause/obligation records and traceability links.
5. Add benchmarked AI extraction and PBI generation.
6. Add authenticated, idempotent Azure DevOps publishing and read-back verification.
