"""Agent harness API schemas."""

from pydantic import BaseModel, ConfigDict, Field

from app.agents.types import (
    AgentRunResult,
    AgentTaskRequest,
    HarnessSpec,
    SelectionResult,
)


class AgentSelectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: str = Field(min_length=1, max_length=4000)
    task_kind: str | None = None


class AgentRegistryResponse(BaseModel):
    harnesses: list[HarnessSpec]


class AgentSelectResponse(BaseModel):
    selection: SelectionResult


class AgentRunRequest(AgentTaskRequest):
    pass


class AgentRunResponse(AgentRunResult):
    pass
