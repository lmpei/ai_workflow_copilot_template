from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate
from app.services import workspace_service
from app.services.public_demo_service import PublicDemoLimitError

router = APIRouter()

WORKSPACE_NOT_FOUND_DETAIL = "未找到工作区"


@router.get("/workspaces", response_model=list[WorkspaceResponse])
async def list_workspaces(
    current_user: User = Depends(get_current_user),
) -> list[WorkspaceResponse]:
    return workspace_service.list_workspaces(user_id=current_user.id)


@router.post("/workspaces", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
) -> WorkspaceResponse:
    try:
        return workspace_service.create_workspace(payload=payload, owner_id=current_user.id)
    except PublicDemoLimitError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.get("/workspaces/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
) -> WorkspaceResponse:
    workspace = workspace_service.get_workspace(workspace_id=workspace_id, user_id=current_user.id)
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=WORKSPACE_NOT_FOUND_DETAIL)
    return workspace


@router.patch("/workspaces/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: str,
    payload: WorkspaceUpdate,
    current_user: User = Depends(get_current_user),
) -> WorkspaceResponse:
    workspace = workspace_service.update_workspace(
        workspace_id=workspace_id,
        user_id=current_user.id,
        payload=payload,
    )
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=WORKSPACE_NOT_FOUND_DETAIL)
    return workspace


@router.delete("/workspaces/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
) -> None:
    deleted = workspace_service.delete_workspace(
        workspace_id=workspace_id,
        user_id=current_user.id,
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=WORKSPACE_NOT_FOUND_DETAIL)
