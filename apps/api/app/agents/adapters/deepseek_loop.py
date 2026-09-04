"""DeepSeek CRS loop-engineering adapter (local token profile, no remote call)."""

from __future__ import annotations

from typing import Any

from app.agents.enforcement.tokens import compact_context
from app.agents.types import AgentTaskRequest, HarnessId, SelectionResult


class DeepSeekLoopAdapter:
    harness_id = HarnessId.DEEPSEEK_LOOP

    def execute(
        self,
        *,
        request: AgentTaskRequest,
        selection: SelectionResult,
        optimized_text: str,
        chunks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        profile = {
            "compact": True,
            "omitContextInSystemPrompt": True,
            "scopedSourceChunks": min(6, len(chunks)),
            "prevOutputLimit": 400,
        }
        context_line = compact_context(request.intent)
        scoped = [
            compact_context(chunk.get("text", ""), 180)
            for chunk in chunks[: profile["scopedSourceChunks"]]
        ]
        loop_steps = [
            "scope",
            "intake",
            "govern",
            "decompose",
            "qc",
            "evidence",
        ]
        return {
            "status": "completed-local",
            "harness_id": self.harness_id.value,
            "review_disposition": "needs-review",
            "profile": profile,
            "context_line": context_line,
            "scoped_sources": scoped,
            "loop": loop_steps,
            "graph": selection.spec.graph,
            "optimized_chars": len(optimized_text),
            "notes": [
                "Local DeepSeek token profile applied; no remote model call.",
                "Outputs are draft. SME/QA/RA review required.",
            ],
        }
