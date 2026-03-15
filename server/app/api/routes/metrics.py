from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.analytics import TraceResponse, WorkspaceAnalyticsResponse
from app.services.trace_service import (
    TraceAccessError,
    get_workspace_analytics,
    get_workspace_metrics,
    list_workspace_traces,
)

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


@router.get(
    "/workspaces/{workspace_id}/analytics",
    response_model=WorkspaceAnalyticsResponse,
)
async def get_analytics(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
) -> WorkspaceAnalyticsResponse:
    try:
        return get_workspace_analytics(workspace_id=workspace_id, user_id=current_user.id)
    except TraceAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get(
    "/workspaces/{workspace_id}/traces",
    response_model=list[TraceResponse],
)
async def get_traces(
    workspace_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
) -> list[TraceResponse]:
    try:
        return list_workspace_traces(
            workspace_id=workspace_id,
            user_id=current_user.id,
            limit=limit,
        )
    except TraceAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
