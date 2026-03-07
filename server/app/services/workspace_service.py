from app.repositories import workspace_repository
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate


def list_workspaces() -> list[WorkspaceResponse]:
    workspaces = workspace_repository.list_workspaces()
    return [WorkspaceResponse.from_model(workspace) for workspace in workspaces]


def get_workspace(workspace_id: str) -> WorkspaceResponse | None:
    workspace = workspace_repository.get_workspace(workspace_id)
    if workspace is None:
        return None
    return WorkspaceResponse.from_model(workspace)


def create_workspace(payload: WorkspaceCreate) -> WorkspaceResponse:
    workspace = workspace_repository.create_workspace(payload=payload)
    return WorkspaceResponse.from_model(workspace)


def update_workspace(workspace_id: str, payload: WorkspaceUpdate) -> WorkspaceResponse | None:
    workspace = workspace_repository.update_workspace(workspace_id=workspace_id, payload=payload)
    if workspace is None:
        return None
    return WorkspaceResponse.from_model(workspace)
