from datetime import UTC, datetime
from uuid import uuid4

from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate

_WORKSPACES: list[Workspace] = []


def list_workspaces() -> list[Workspace]:
    return list(_WORKSPACES)


def get_workspace(workspace_id: str) -> Workspace | None:
    for workspace in _WORKSPACES:
        if workspace.id == workspace_id:
            return workspace
    return None


def create_workspace(payload: WorkspaceCreate, owner_id: str = "demo-user") -> Workspace:
    now = datetime.now(UTC)
    workspace = Workspace(
        id=str(uuid4()),
        owner_id=owner_id,
        name=payload.name,
        type=payload.type or "research",
        description=payload.description,
        created_at=now,
        updated_at=now,
    )
    _WORKSPACES.append(workspace)
    return workspace


def update_workspace(workspace_id: str, payload: WorkspaceUpdate) -> Workspace | None:
    workspace = get_workspace(workspace_id)
    if workspace is None:
        return None

    changed = False
    if payload.name is not None:
        workspace.name = payload.name
        changed = True
    if payload.type is not None:
        workspace.type = payload.type
        changed = True
    if payload.description is not None:
        workspace.description = payload.description
        changed = True
    if changed:
        workspace.updated_at = datetime.now(UTC)
    return workspace
