"""Placeholder agent routes.

The live platform executes scenario work through task-scoped worker flows.
Direct durable agent APIs are intentionally left scaffolded until the runtime
contract for standalone agent runs exists.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.services.agent_service import run_agent_preview

router = APIRouter()


class AgentRunRequest(BaseModel):
    agent_name: str
    goal: str


@router.post("/workspaces/{workspace_id}/agents/run", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def run_agent(workspace_id: str, payload: AgentRunRequest) -> dict:
    preview = run_agent_preview(goal=payload.goal)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "status": "scaffolded",
            "message": (
                "This route is a placeholder. The current platform supports "
                "task-scoped agent execution only; direct durable agent runs are not implemented."
            ),
            "workspace_id": workspace_id,
            "agent_name": payload.agent_name,
            "preview": preview,
        },
    )


@router.get("/agent-runs/{run_id}", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def get_agent_run(run_id: str) -> dict:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "status": "scaffolded",
            "message": (
                "This route is a placeholder. Agent run history is available "
                "only through task-scoped execution records today."
            ),
            "run_id": run_id,
        },
    )
