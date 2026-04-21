from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.workspace import Workspace
from app.schemas.scenario import (
    MODULE_TYPE_RESEARCH,
    is_supported_module_type,
    merge_module_config,
)


def _validate_supported_module_type(module_type: str | None) -> str | None:
    if module_type is None:
        return None
    if not is_supported_module_type(module_type):
        raise ValueError(f"Unsupported module type: {module_type}")
    return module_type


class WorkspaceCreate(BaseModel):
    name: str
    # Deprecated compatibility alias. New callers should send module_type only.
    type: str | None = None
    module_type: str | None = None
    description: str | None = None
    module_config_json: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_module_contract(self) -> "WorkspaceCreate":
        self.type = _validate_supported_module_type(self.type)
        self.module_type = _validate_supported_module_type(self.module_type)

        if self.type and self.module_type and self.type != self.module_type:
            raise ValueError("Workspace type and module type must match")

        if self.type is None and self.module_type is None:
            self.type = MODULE_TYPE_RESEARCH
            self.module_type = MODULE_TYPE_RESEARCH
        elif self.type is None:
            self.type = self.module_type
        elif self.module_type is None:
            self.module_type = self.type

        return self


class WorkspaceUpdate(BaseModel):
    name: str | None = None
    # Deprecated compatibility alias. New callers should send module_type only.
    type: str | None = None
    module_type: str | None = None
    description: str | None = None
    module_config_json: dict[str, object] | None = None

    @model_validator(mode="after")
    def validate_module_contract(self) -> "WorkspaceUpdate":
        self.type = _validate_supported_module_type(self.type)
        self.module_type = _validate_supported_module_type(self.module_type)

        if self.type and self.module_type and self.type != self.module_type:
            raise ValueError("Workspace type and module type must match")

        if self.type is None and self.module_type is not None:
            self.type = self.module_type
        elif self.module_type is None and self.type is not None:
            self.module_type = self.type

        return self


class WorkspaceResponse(BaseModel):
    id: str
    owner_id: str
    name: str
    module_type: str
    description: str | None = None
    module_config_json: dict[str, object]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, workspace: Workspace) -> "WorkspaceResponse":
        return cls(
            id=workspace.id,
            owner_id=workspace.owner_id,
            name=workspace.name,
            module_type=workspace.module_type,
            description=workspace.description,
            module_config_json=merge_module_config(
                workspace.module_type,
                workspace.module_config_json,
            ),
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
        )
