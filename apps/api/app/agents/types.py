"""Shared types for agent harness auto-selection."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field


class TaskKind(StrEnum):
    LOOP_ENGINEERING = "loop_engineering"
    ORCHESTRATION_COMPLIANCE = "orchestration_compliance"
    RAG = "rag"
    INFRA = "infra"
    SKILL_ORCHESTRATION = "skill_orchestration"
    IDEA_TO_APP = "idea_to_app"


class HarnessId(StrEnum):
    DEEPSEEK_LOOP = "deepseek_loop"
    LANGGRAPH_LANGSMITH_GUARDRAILS = "langgraph_langsmith_guardrails"
    LLAMAINDEX_RAG = "llamaindex_rag"
    REDIS_MEMBRANE_HTMX = "redis_membrane_htmx"
    SEMANTIC_KERNEL = "semantic_kernel"
    TRANSFORMERLAB = "transformerlab"


class ReviewDisposition(StrEnum):
    NEEDS_REVIEW = "needs-review"
    GAP_REQUIRES_REVIEW = "gap-requires-review"


class ActorContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actor: str = Field(min_length=1, max_length=256)
    role: str = Field(min_length=1, max_length=64)
    send_external: bool = False


class AgentTaskRequest(BaseModel):
    """Inbound task. Optional task_kind overrides auto-select."""

    model_config = ConfigDict(extra="forbid")

    intent: str = Field(min_length=1, max_length=4000)
    task_kind: TaskKind | None = None
    actor: str = Field(min_length=1, max_length=256)
    role: str = Field(min_length=1, max_length=64)
    payload: dict[str, Any] = Field(default_factory=dict)
    document_id: int | None = None
    send_external: bool = False
    schema_name: str | None = None


class HarnessSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    harness_id: HarnessId
    task_kind: TaskKind
    vendor_stack: list[str]
    adapter: str
    graph: str
    local_only_default: bool = True
    description: str


class SelectionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_kind: TaskKind
    harness_id: HarnessId
    spec: HarnessSpec
    inferred_kind: TaskKind
    explicit_kind: TaskKind | None
    matched_signals: list[str]
    review_disposition: ReviewDisposition = ReviewDisposition.NEEDS_REVIEW


class TokenOptimizationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    original_tokens: int
    optimized_tokens: int
    chunks: int
    duplicates_removed: int
    compact_context_chars: int


class EnforcementReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_valid: bool
    authorized: bool
    audit_event_id: int | None = None
    token_optimization: TokenOptimizationReport | None = None
    blocked_reason: str | None = None
    data_governance: str = "local-derived-only"


class AgentRunResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    selection: SelectionResult
    enforcement: EnforcementReport
    output: dict[str, Any]
    review_disposition: ReviewDisposition = ReviewDisposition.NEEDS_REVIEW
    notes: list[str] = Field(default_factory=list)


class HarnessAdapter(Protocol):
    harness_id: HarnessId

    def execute(
        self,
        *,
        request: AgentTaskRequest,
        selection: SelectionResult,
        optimized_text: str,
        chunks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        ...
