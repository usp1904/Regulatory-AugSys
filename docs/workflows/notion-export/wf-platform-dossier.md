# Evidence-based dossier export

**Workflow ID:** WF-PLATFORM-DOSSIER
**Graph:** Approved evidence → CTD order → Render → Manifest → Immutable file → Audit

## MVP traceability

- MVP-24

## API

- `POST /api/v1/dossiers/{dossier_id}/export`
- `GET /api/v1/dossier-exports/{export_id}/download`

## Web routes

- `/dossiers`

## Export formats

- txt
- docx
- pdf

## Verification

- `apps/api/tests/test_dossier_export.py`
