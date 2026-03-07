from fastapi import APIRouter

from app.services.trace_service import get_metrics_snapshot

router = APIRouter()


@router.get("/workspaces/{workspace_id}/metrics")
async def get_metrics(workspace_id: str) -> dict:
    return get_metrics_snapshot(workspace_id=workspace_id)
