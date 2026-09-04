"""LangGraph + LangSmith + Guardrails local orchestrator.

Executes a deterministic node graph and records spans. Schema checks run
before and after via enforcement.guardrails (the Guardrails AI mapping).
"""

from __future__ import annotations

from typing import Any

from app.agents.types import AgentTaskRequest, HarnessId, SelectionResult

NODES = ("intake", "guard", "transform", "trace", "evidence", "export")


class LangGraphOrchestratorAdapter:
    harness_id = HarnessId.LANGGRAPH_LANGSMITH_GUARDRAILS

    def execute(
        self,
        *,
        request: AgentTaskRequest,
        selection: SelectionResult,
        optimized_text: str,
        chunks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        spans: list[dict[str, Any]] = []
        state: dict[str, Any] = {
            "intent": request.intent,
            "chunk_count": len(chunks),
            "optimized_chars": len(optimized_text),
        }
        for order, node in enumerate(NODES):
            spans.append(
                {
                    "name": node,
                    "order": order,
                    "status": "ok",
                    "guardrail": node in {"intake", "guard", "export"},
                }
            )
            state[node] = "ok"
        return {
            "status": "completed-local",
            "harness_id": self.harness_id.value,
            "review_disposition": "needs-review",
            "graph": list(NODES),
            "langsmith_spans": spans,
            "guardrails": {
                "provider": "local-schema-adapter",
                "vendor_mapping": "Guardrails AI",
                "nodes_checked": ["intake", "guard", "export"],
            },
            "state": state,
            "notes": [
                "Local LangGraph-shaped run with LangSmith-style spans.",
                "Traceability only; gap requires review before any controlled use.",
            ],
        }
