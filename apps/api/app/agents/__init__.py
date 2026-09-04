"""Platform agent auto-selection and enforcement.

Task intent maps to a required harness. Enforcement (schema guardrails,
authorization, audit logging, semantic chunking + deduplication) runs on
every execute path. Vendor SDKs are optional; local adapters are the default.
"""

from app.agents.registry import HARNESS_REGISTRY, get_harness
from app.agents.runner import run_agent_task
from app.agents.selector import select_harness

__all__ = [
    "HARNESS_REGISTRY",
    "get_harness",
    "run_agent_task",
    "select_harness",
]
