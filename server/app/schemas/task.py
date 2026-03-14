from datetime import datetime

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    task_type: str
    input: dict = Field(default_factory=dict)


class TaskResponse(BaseModel):
    id: str
    workspace_id: str
    task_type: str
    status: str
    created_by: str
    input_json: dict
    output_json: dict
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
            created_by=task.created_by,
            input_json=task.input_json,
            output_json=task.output_json,
            error_message=task.error_message,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
