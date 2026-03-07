from datetime import datetime

from pydantic import BaseModel

from app.models.workspace import Workspace


class WorkspaceCreate(BaseModel):
    name: str
    type: str | None = None
    description: str | None = None


class WorkspaceUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    description: str | None = None


class WorkspaceResponse(BaseModel):
    id: str
    owner_id: str
    name: str
    type: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, workspace: Workspace) -> "WorkspaceResponse":
        return cls(
            id=workspace.id,
            owner_id=workspace.owner_id,
            name=workspace.name,
            type=workspace.type,
            description=workspace.description,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
        )
