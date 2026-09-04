"""Policy registry: task kind → required harness.

Auto-selection consults this table. Changing mappings here is the only
supported way to retarget a task family.
"""

from __future__ import annotations

from app.agents.types import HarnessId, HarnessSpec, TaskKind

HARNESS_REGISTRY: dict[TaskKind, HarnessSpec] = {
    TaskKind.LOOP_ENGINEERING: HarnessSpec(
        harness_id=HarnessId.DEEPSEEK_LOOP,
        task_kind=TaskKind.LOOP_ENGINEERING,
        vendor_stack=["DeepSeek"],
        adapter="app.agents.adapters.deepseek_loop.DeepSeekLoopAdapter",
        graph="Scope → Intake → Govern → Decompose → QC → Evidence",
        description="CRS loop engineering with compact DeepSeek token profile.",
    ),
    TaskKind.ORCHESTRATION_COMPLIANCE: HarnessSpec(
        harness_id=HarnessId.LANGGRAPH_LANGSMITH_GUARDRAILS,
        task_kind=TaskKind.ORCHESTRATION_COMPLIANCE,
        vendor_stack=["LangGraph", "LangSmith", "Guardrails AI"],
        adapter="app.agents.adapters.langgraph_orchestrator.LangGraphOrchestratorAdapter",
        graph="Intake → Guard → Transform → Trace → Evidence → Export",
        description="Orchestration graph with local LangSmith-style traces and schema guards.",
    ),
    TaskKind.RAG: HarnessSpec(
        harness_id=HarnessId.LLAMAINDEX_RAG,
        task_kind=TaskKind.RAG,
        vendor_stack=["LlamaIndex"],
        adapter="app.agents.adapters.llamaindex_rag.LlamaIndexRagAdapter",
        graph="Extract (derived) → Clean → OKF v0.2 → Chunk → Dedup → Index (local)",
        description="LlamaIndex-shaped local index over derived extracts only.",
    ),
    TaskKind.INFRA: HarnessSpec(
        harness_id=HarnessId.REDIS_MEMBRANE_HTMX,
        task_kind=TaskKind.INFRA,
        vendor_stack=["Redis", "Membrane", "HTMX"],
        adapter="app.agents.adapters.infra_stack.RedisMembraneHtmxAdapter",
        graph="Request → Membrane policy → Cache → HTMX fragment",
        description="In-process Redis-shaped cache, Membrane allowlist, and HTMX contract.",
    ),
    TaskKind.SKILL_ORCHESTRATION: HarnessSpec(
        harness_id=HarnessId.SEMANTIC_KERNEL,
        task_kind=TaskKind.SKILL_ORCHESTRATION,
        vendor_stack=["Semantic Kernel"],
        adapter="app.agents.adapters.semantic_kernel.SemanticKernelAdapter",
        graph="Intent → Plugin map → Skill invoke → Citation gate",
        description="Maps platform Cursor skills to Semantic Kernel-shaped plugins.",
    ),
    TaskKind.IDEA_TO_APP: HarnessSpec(
        harness_id=HarnessId.TRANSFORMERLAB,
        task_kind=TaskKind.IDEA_TO_APP,
        vendor_stack=["TransformerLab"],
        adapter="app.agents.adapters.transformerlab.TransformerLabAdapter",
        graph="Idea → Spec → Module sketch → Review (draft)",
        description="Local idea-to-app conversion plan; no remote training or model upload.",
    ),
}


def get_harness(task_kind: TaskKind) -> HarnessSpec:
    return HARNESS_REGISTRY[task_kind]


def list_registry() -> list[HarnessSpec]:
    return list(HARNESS_REGISTRY.values())
