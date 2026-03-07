from fastapi import APIRouter, HTTPException, status

from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate
from app.services import workspace_service

router = APIRouter()


@router.get("/workspaces", response_model=list[WorkspaceResponse])
async def list_workspaces() -> list[WorkspaceResponse]:
    return workspace_service.list_workspaces()


@router.post("/workspaces", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(payload: WorkspaceCreate) -> WorkspaceResponse:
    return workspace_service.create_workspace(payload=payload)


@router.get("/workspaces/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(workspace_id: str) -> WorkspaceResponse:
    workspace = workspace_service.get_workspace(workspace_id)
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return workspace


@router.patch("/workspaces/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(workspace_id: str, payload: WorkspaceUpdate) -> WorkspaceResponse:
    workspace = workspace_service.update_workspace(workspace_id=workspace_id, payload=payload)
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return workspace
