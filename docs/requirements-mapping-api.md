# Requirements Mapping API — persistent draft workflow

This slice adds persistent requirements-mapping records to the existing FastAPI + SQLAlchemy platform. It does not require a Firebase project; the current PostgreSQL/SQLite persistence layer is reused so the project can be configured later without creating a second data store.

## Endpoints

- `POST /api/v1/requirements-mappings` — create a draft mapping. The API does not accept client-side approval as authoritative; review starts as `PENDING`.
- `GET /api/v1/requirements-mappings?dossier_id=...` — list mappings, optionally scoped to a dossier.
- `GET /api/v1/requirements-mappings/{id}` — retrieve a mapping.
- `POST /api/v1/requirements-mappings/{id}/review` — record a reviewer decision. Approval is rejected with HTTP 409 while completeness blockers remain.

## Data and controls

- Mapping body is stored as JSON text, preserving the source, obligation, system finding/evidence, clarification, requirement, PBI, acceptance criteria, and test evidence fields.
- Mapping records and review decisions produce audit events with actor, event type, and mapping key.
- Readiness is computed from the stored data on response; client-supplied readiness labels are not trusted.
- An unresolved interpretation, unfinalized applicability, unreviewed source, missing evidence, open dependency, missing test evidence, or incomplete PBI blocks approval.
- Reviewer identity is currently supplied by the request. This is **not authentication** and must not be treated as proof of who made the decision.

## Database migration

Run from `apps/api`:

```bash
alembic upgrade head
```

The migration adds the `requirements_mappings` table and indexes. Test fixtures create tables from SQLAlchemy metadata in an isolated SQLite database.

## Test coverage

`tests/test_requirements_mapping.py` covers persistence, draft status, audit events, rejection of approval when the decision is unresolved, successful approval when all gates pass, dossier filtering, and 404 handling.

## Known production gaps

- Authentication and role-based authorization are not implemented for these new routes.
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
