"""Intent → task kind → harness auto-selection.

Deterministic keyword scoring. No external LLM. Explicit task_kind wins
when provided and registered; inferred kind is still recorded for audit.
"""

from __future__ import annotations

import re

from app.agents.registry import get_harness
from app.agents.types import ReviewDisposition, SelectionResult, TaskKind

_SIGNAL_TABLE: tuple[tuple[TaskKind, tuple[str, ...]], ...] = (
    (
        TaskKind.LOOP_ENGINEERING,
        (
            "loop engineering",
            "crs",
            "deepseek",
            "decompose",
            "retry loop",
            "harness context",
            "token profile",
            "iterate until",
        ),
    ),
    (
        TaskKind.ORCHESTRATION_COMPLIANCE,
        (
            "langgraph",
            "langsmith",
            "guardrails",
            "orchestrat",
            "workflow graph",
            "compliance gate",
            "trace span",
        ),
    ),
    (
        TaskKind.RAG,
        (
            "rag",
            "llamaindex",
            "retriev",
            "okf",
            "chunk",
            "embedding",
            "vector",
            "document tree",
            "semantic chunk",
        ),
    ),
    (
        TaskKind.INFRA,
        (
            "redis",
            "membrane",
            "htmx",
            "cache",
            "infra",
            "websocket",
            "session store",
        ),
    ),
    (
        TaskKind.SKILL_ORCHESTRATION,
        (
            "semantic kernel",
            "skill orchestr",
            "plugin",
            "invoke skill",
            "cursor skill",
        ),
    ),
    (
        TaskKind.IDEA_TO_APP,
        (
            "transformerlab",
            "idea-to-app",
            "idea to app",
            "prototype app",
            "convert this idea",
            "scaffold app",
        ),
    ),
)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def infer_task_kind(intent: str) -> tuple[TaskKind, list[str]]:
    blob = _normalize(intent)
    scores: dict[TaskKind, list[str]] = {kind: [] for kind, _ in _SIGNAL_TABLE}
    for kind, signals in _SIGNAL_TABLE:
        for signal in signals:
            if signal in blob:
                scores[kind].append(signal)
    ranked = sorted(scores.items(), key=lambda item: len(item[1]), reverse=True)
    top_kind, top_hits = ranked[0]
    if not top_hits:
        return TaskKind.ORCHESTRATION_COMPLIANCE, []
    return top_kind, top_hits


def select_harness(intent: str, explicit_kind: TaskKind | None = None) -> SelectionResult:
    inferred, signals = infer_task_kind(intent)
    kind = explicit_kind or inferred
    spec = get_harness(kind)
    return SelectionResult(
        task_kind=kind,
        harness_id=spec.harness_id,
        spec=spec,
        inferred_kind=inferred,
        explicit_kind=explicit_kind,
        matched_signals=signals,
        review_disposition=ReviewDisposition.NEEDS_REVIEW,
    )
