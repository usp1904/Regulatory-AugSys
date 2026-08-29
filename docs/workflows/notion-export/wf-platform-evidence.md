# Evidence capture and human review

**Workflow ID:** WF-PLATFORM-EVIDENCE
**Graph:** Capture → Pending → Review → Approved | Rejected | Needs clarification

## MVP traceability

- MVP-23

## API

- `POST /api/v1/evidence`
- `PATCH /api/v1/evidence/{id}`
- `POST /api/v1/evidence/{id}/review`
- `GET /api/v1/evidence/{id}/review-context`

## Web routes

- `/documents/{id}`
- `/evidence/review/{id}`

## Business rules

- Approved excerpt immutable; changes create new version
- Only APPROVED evidence in exports

## Verification

- `apps/api/tests/test_evidence.py`
