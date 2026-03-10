from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.user import User
from app.services.trace_service import TraceAccessError, get_workspace_metrics

router = APIRouter()


@router.get("/workspaces/{workspace_id}/metrics")
async def get_metrics(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
) -> dict:
    try:
        return get_workspace_metrics(workspace_id=workspace_id, user_id=current_user.id)
    except TraceAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
