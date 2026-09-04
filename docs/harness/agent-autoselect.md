# Agent harness auto-select (local adapters)

Runtime code: `apps/api/app/agents/`. This document maps vendor names to **local default adapters**. Vendor SDKs are not required to execute auto-select or enforcement.

## Auto-select

```text
Intent → keyword score → TaskKind → HARNESS_REGISTRY → adapter
```

Explicit `task_kind` on `POST /api/v1/agents/run` wins; inferred kind is still stored on the audit event.

| Task kind | Required harness | Local adapter |
|-----------|------------------|---------------|
| `loop_engineering` | DeepSeek | `DeepSeekLoopAdapter` |
| `orchestration_compliance` | LangGraph + LangSmith + Guardrails AI | `LangGraphOrchestratorAdapter` + `enforcement.guardrails` |
| `rag` | LlamaIndex | `LlamaIndexRagAdapter` + `okf_pipeline` |
| `infra` | Redis + Membrane + HTMX | `RedisMembraneHtmxAdapter` |
| `skill_orchestration` | Semantic Kernel | `SemanticKernelAdapter` |
| `idea_to_app` | TransformerLab | `TransformerLabAdapter` |

## Enforcement (every run)

```text
Authz → Guardrails schema → Semantic chunk + Jaccard dedup → Adapter → Output schema → Audit
```

- **Guardrails:** local schema adapter (forbidden autonomous-approval language; required RAG extract).
- **Access control:** named actor + allowlisted role; `unknown`/`guest` blocked. Denied attempts emit `agent_run_denied`.
- **Audit:** `agent_run` / `agent_run_denied` on `audit_events` (traceability, not approval).
- **Token optimization:** 500–1000 token chunks, Jaccard ≥ 0.92 paragraph drop, 280-char compact context.
- **Data governance:** `DATA_GOVERNANCE_ALLOW_EXTERNAL=false` by default; extracts/embeddings/prompts are not sent to external APIs.

## RAG / OKF

RAG uses `Document.full_extracted_text()` (derived pages/paragraphs) or `payload.text`. Original `storage_path` files are not opened or rewritten.

## Review language

Adapter outputs use `review_disposition: needs-review`. Evidence indicates a local run completed; gap requires review; SME/QA/RA review required.
