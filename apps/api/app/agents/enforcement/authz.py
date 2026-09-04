"""Authorization gate for agent runs.

Blocks anonymous, unknown, and unlisted roles. Does not claim cybersecurity
certification; it is an access-control check for this API process.
"""

from __future__ import annotations

from app.agents.enforcement.exceptions import DataGovernanceError, UnauthorizedAgentAccess
from app.agents.types import AgentTaskRequest
from app.core.config import get_settings

ALLOWED_ROLES = frozenset(
    {
        "sme",
        "qa",
        "ra",
        "system-owner",
        "developer",
        "internal-audit",
    }
)

BLOCKED_ACTORS = frozenset({"", "unknown", "anonymous", "anon", "guest"})


def authorize_agent_request(request: AgentTaskRequest) -> None:
    actor = request.actor.strip().lower()
    role = request.role.strip().lower()
    if actor in BLOCKED_ACTORS:
        raise UnauthorizedAgentAccess("Unauthorized agent access blocked: actor identity required")
    if role not in ALLOWED_ROLES:
        raise UnauthorizedAgentAccess(
            f"Unauthorized agent access blocked: role {role!r} is not permitted"
        )
    settings = get_settings()
    if request.send_external and not settings.data_governance_allow_external:
        raise DataGovernanceError(
            "External transmission of source documents, extracts, embeddings, "
            "prompts, or metadata is blocked unless data-governance policy permits it"
        )
