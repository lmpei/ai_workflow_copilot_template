from datetime import datetime

from pydantic import BaseModel, Field

from app.core.runtime_control import build_recovery_detail, derive_recovery_state


class TaskCreate(BaseModel):
    task_type: str
    input: dict = Field(default_factory=dict)


class TaskControlRequest(BaseModel):
    reason: str | None = None


class TaskResponse(BaseModel):
    id: str
    workspace_id: str
    task_type: str
    status: str
    recovery_state: str
    recovery_detail: dict[str, object]
    created_by: str
    input_json: dict
    output_json: dict
    control_json: dict
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, task) -> "TaskResponse":
        return cls(
            id=task.id,
            workspace_id=task.workspace_id,
            task_type=task.task_type,
            status=task.status,
            recovery_state=derive_recovery_state(status=task.status, control_json=task.control_json),
            recovery_detail=build_recovery_detail(status=task.status, control_json=task.control_json),
            created_by=task.created_by,
            input_json=task.input_json,
            output_json=task.output_json,
            control_json=task.control_json,
            error_message=task.error_message,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
