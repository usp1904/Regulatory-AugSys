"""Redis + Membrane + HTMX infra adapter (in-process defaults)."""

from __future__ import annotations

from typing import Any

from app.agents.types import AgentTaskRequest, HarnessId, SelectionResult

_CACHE: dict[str, str] = {}

ALLOWED_ROUTES = frozenset(
    {
        "/api/v1/agents/select",
        "/api/v1/agents/run",
        "/api/v1/agents/registry",
        "/health",
    }
)


class RedisMembraneHtmxAdapter:
    harness_id = HarnessId.REDIS_MEMBRANE_HTMX

    def execute(
        self,
        *,
        request: AgentTaskRequest,
        selection: SelectionResult,
        optimized_text: str,
        chunks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        route = str(request.payload.get("route") or "/api/v1/agents/run")
        membrane_allow = route in ALLOWED_ROUTES
        cache_key = str(request.payload.get("cache_key") or request.intent[:64])
        if membrane_allow:
            _CACHE[cache_key] = optimized_text[:500]
        fragment = (
            f'<section hx-get="{route}" hx-swap="innerHTML">'
            f"<p>cache={'hit' if cache_key in _CACHE else 'miss'}</p>"
            f"<p>chunks={len(chunks)}</p>"
            "</section>"
        )
        return {
            "status": "completed-local" if membrane_allow else "blocked-local",
            "harness_id": self.harness_id.value,
            "review_disposition": "needs-review",
            "redis": {"backend": "in-process-dict", "keys": len(_CACHE), "stored": membrane_allow},
            "membrane": {"route": route, "allowed": membrane_allow, "policy": "allowlist"},
            "htmx": {"fragment": fragment, "swap": "innerHTML"},
            "graph": selection.spec.graph,
            "notes": [
                "In-process Redis-shaped cache; not a clustered Redis deployment.",
                "Membrane deny is an application allowlist, not a network firewall claim.",
            ],
        }
