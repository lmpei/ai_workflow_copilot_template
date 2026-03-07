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
            "message": "Durable LangGraph execution is planned for Phase 3 Tasks + Agents.",
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
            "message": "Agent run history is planned for Phase 3 with persistence and tracing.",
            "run_id": run_id,
        },
    )
