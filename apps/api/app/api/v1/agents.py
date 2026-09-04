"""Agent auto-select and enforced run routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.enforcement.exceptions import AgentEnforcementError
from app.agents.registry import list_registry
from app.agents.runner import run_agent_task
from app.agents.selector import select_harness
from app.agents.types import AgentTaskRequest, TaskKind
from app.core.database import get_db
from app.schemas.agent import (
    AgentRegistryResponse,
    AgentRunRequest,
    AgentRunResponse,
    AgentSelectRequest,
    AgentSelectResponse,
)
from app.services.audit import record_audit_event

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/registry", response_model=AgentRegistryResponse)
def get_registry() -> AgentRegistryResponse:
    return AgentRegistryResponse(harnesses=list_registry())


@router.post("/select", response_model=AgentSelectResponse)
def select_agent(payload: AgentSelectRequest) -> AgentSelectResponse:
    explicit: TaskKind | None = None
    if payload.task_kind:
        try:
            explicit = TaskKind(payload.task_kind)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Unknown task_kind") from exc
    return AgentSelectResponse(selection=select_harness(payload.intent, explicit))


@router.post("/run", response_model=AgentRunResponse)
def run_agent(payload: AgentRunRequest, db: Session = Depends(get_db)) -> AgentRunResponse:
    request = AgentTaskRequest.model_validate(payload.model_dump())
    try:
        return run_agent_task(db, request)
    except AgentEnforcementError as exc:
        record_audit_event(
            db,
            event_type="agent_run_denied",
            actor=request.actor or "unknown",
            document_id=request.document_id,
            detail={
                "reason": str(exc),
                "http_status": exc.http_status,
                "intent": request.intent[:280],
            },
        )
        db.commit()
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc
