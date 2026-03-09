from app.repositories import workspace_repository
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate


def list_workspaces(user_id: str) -> list[WorkspaceResponse]:
    workspaces = workspace_repository.list_workspaces(user_id=user_id)
    return [WorkspaceResponse.from_model(workspace) for workspace in workspaces]


def get_workspace(workspace_id: str, user_id: str) -> WorkspaceResponse | None:
    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        return None
    return WorkspaceResponse.from_model(workspace)


def create_workspace(payload: WorkspaceCreate, owner_id: str) -> WorkspaceResponse:
    workspace = workspace_repository.create_workspace(payload=payload, owner_id=owner_id)
    return WorkspaceResponse.from_model(workspace)


def update_workspace(
    workspace_id: str,
    user_id: str,
    payload: WorkspaceUpdate,
) -> WorkspaceResponse | None:
    workspace = workspace_repository.update_workspace(
        workspace_id=workspace_id,
        user_id=user_id,
        payload=payload,
    )
    if workspace is None:
        return None
    return WorkspaceResponse.from_model(workspace)
