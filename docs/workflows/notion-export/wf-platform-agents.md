# Agent harness auto-select and enforcement

**Workflow ID:** WF-PLATFORM-AGENTS
**Graph:** Intent → Select harness → Authz → Guardrails → Chunk/dedup → Adapter → Audit

## MVP traceability

- MVP-21
- MVP-26

## Harness (token optimization)

- auto-select registry in apps/api/app/agents/registry.py

## Token rules

- semantic chunking 500–1000 tokens
- Jaccard near-duplicate removal
- compact context 280 chars

## API

- `GET /api/v1/agents/registry`
- `POST /api/v1/agents/select`
- `POST /api/v1/agents/run`

## Business rules

- Original source files remain immutable; RAG uses derived extracts only
- Denied and successful runs write audit events
- Outputs remain needs-review; no autonomous approval

## Verification

- `apps/api/tests/test_agent_autoselect.py`
- `pytest`
