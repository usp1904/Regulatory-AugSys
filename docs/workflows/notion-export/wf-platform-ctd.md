# CTD Module 3.2.S validation

**Workflow ID:** WF-PLATFORM-CTD
**Graph:** Documents → Framework/Jurisdiction scope → Validate → Gap report

## MVP traceability

- MVP-22

## API

- `POST /api/v1/ctd-engine/validate`
- `GET /api/v1/ctd-sections`

## Web routes

- `/ctd`

## Verification

- `apps/api/tests/test_ctd_engine.py`
- `apps/api/tests/test_ctd_sections.py`
