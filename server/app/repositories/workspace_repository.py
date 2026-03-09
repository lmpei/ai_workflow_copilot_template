from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select

from app.core.database import session_scope
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate


def list_workspaces(user_id: str) -> list[Workspace]:
    with session_scope() as session:
        statement = (
            select(Workspace)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(WorkspaceMember.user_id == user_id)
            .order_by(Workspace.created_at.asc())
        )
        result = session.scalars(statement)
        return list(result)


def get_workspace(workspace_id: str, user_id: str) -> Workspace | None:
    with session_scope() as session:
        statement = (
            select(Workspace)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(
                Workspace.id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        return session.scalar(statement)


def create_workspace(payload: WorkspaceCreate, owner_id: str) -> Workspace:
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
    membership = WorkspaceMember(
        id=str(uuid4()),
        workspace_id=workspace.id,
        user_id=owner_id,
        member_role="owner",
        created_at=now,
    )
    with session_scope() as session:
        session.add(workspace)
        session.add(membership)
        session.flush()
        session.refresh(workspace)
        return workspace


def update_workspace(workspace_id: str, user_id: str, payload: WorkspaceUpdate) -> Workspace | None:
    with session_scope() as session:
        statement = (
            select(Workspace)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(
                Workspace.id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        workspace = session.scalar(statement)
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

        session.add(workspace)
        session.flush()
        session.refresh(workspace)
        return workspace
