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
