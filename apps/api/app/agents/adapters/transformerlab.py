"""TransformerLab-shaped idea-to-app conversion (local spec only)."""

from __future__ import annotations

from typing import Any

from app.agents.types import AgentTaskRequest, HarnessId, SelectionResult

MODULES = (
    "api-surface",
    "derived-extract-store",
    "audit-events",
    "review-queue",
)


class TransformerLabAdapter:
    harness_id = HarnessId.TRANSFORMERLAB

    def execute(
        self,
        *,
        request: AgentTaskRequest,
        selection: SelectionResult,
        optimized_text: str,
        chunks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        idea = str(request.payload.get("idea") or request.intent)
        return {
            "status": "completed-local",
            "harness_id": self.harness_id.value,
            "review_disposition": "needs-review",
            "transformerlab": {
                "vendor_mapping": "TransformerLab",
                "mode": "local-spec",
                "idea": idea[:500],
                "modules": list(MODULES),
                "watermark": "DRAFT_NOT_CONTROLLED",
            },
            "app_sketch": {
                "stack": ["FastAPI", "Next.js", "SQLite-or-Postgres"],
                "constraints": [
                    "Do not upload corpora to remote training APIs.",
                    "Keep original sources immutable.",
                    "Exports remain DRAFT_NOT_CONTROLLED.",
                ],
                "chunk_count": len(chunks),
                "optimized_chars": len(optimized_text),
            },
            "graph": selection.spec.graph,
            "notes": [
                "Idea-to-app sketch only. Gap requires review before implementation "
                "in a controlled system.",
            ],
        }
