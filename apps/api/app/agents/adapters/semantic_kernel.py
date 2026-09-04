"""Semantic Kernel-shaped skill orchestration over in-repo Cursor skills."""

from __future__ import annotations

from typing import Any

from app.agents.types import AgentTaskRequest, HarnessId, SelectionResult

SKILL_PLUGINS: dict[str, str] = {
    "regulatory-source-intake": "Register sources with HOLD/DRIVE gates",
    "regulatory-evidence-extraction": "Atomic source-grounded excerpts",
    "requirements-comparator": "Cross-market / SOP comparison",
    "ctd-ectd-mapper": "CTD/eCTD section placement",
    "regulated-document-review": "SME/QA/RA review worksheets",
    "citation-and-provenance-auditor": "Citation and traceability audit",
    "controlled-authoring": "SOP/WI/policy draft packages",
    "data-integrity-checker": "ALCOA+ assessment",
    "regulatory-change-impact": "Source version change impact",
    "validation-test-generator": "IQ/OQ/PQ draft test packages",
}


def _match_skills(intent: str) -> list[str]:
    blob = intent.lower()
    hits: list[str] = []
    for name in SKILL_PLUGINS:
        token = name.split("-")[0]
        if token in blob or name.replace("-", " ") in blob:
            hits.append(name)
    if not hits:
        if "citation" in blob or "provenance" in blob:
            hits.append("citation-and-provenance-auditor")
        elif "ctd" in blob:
            hits.append("ctd-ectd-mapper")
        else:
            hits.append("regulated-document-review")
    return hits


class SemanticKernelAdapter:
    harness_id = HarnessId.SEMANTIC_KERNEL

    def execute(
        self,
        *,
        request: AgentTaskRequest,
        selection: SelectionResult,
        optimized_text: str,
        chunks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        requested = request.payload.get("skills")
        if isinstance(requested, list) and requested:
            selected = [str(item) for item in requested if str(item) in SKILL_PLUGINS]
        else:
            selected = _match_skills(request.intent)
        plan = [
            {
                "plugin": name,
                "purpose": SKILL_PLUGINS[name],
                "status": "planned-local",
            }
            for name in selected
        ]
        return {
            "status": "completed-local",
            "harness_id": self.harness_id.value,
            "review_disposition": "needs-review",
            "semantic_kernel": {
                "vendor_mapping": "Semantic Kernel",
                "plugins": plan,
                "chunk_count": len(chunks),
                "optimized_chars": len(optimized_text),
            },
            "graph": selection.spec.graph,
            "notes": [
                "Skill plan only; validators under .cursor/skills remain the JSON gates.",
                "No skill output is an approval decision. SME/QA/RA review required.",
            ],
        }
