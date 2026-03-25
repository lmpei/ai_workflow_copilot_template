from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.core.runtime_control import build_recovery_detail, derive_recovery_state
from app.models.task import TASK_STATUS_DONE
from app.schemas.scenario import ScenarioTaskType

TaskStatus = Literal["pending", "running", "completed", "failed"]


def _serialize_task_status(status: str) -> TaskStatus:
    if status == TASK_STATUS_DONE:
        return "completed"
    if status == "pending":
        return "pending"
    if status == "running":
        return "running"
    if status == "failed":
        return "failed"
    raise ValueError(f"Unsupported task status: {status}")


def _serialize_recovery_state(recovery_state: str) -> str:
    return "completed" if recovery_state == TASK_STATUS_DONE else recovery_state


def _serialize_recovery_detail(detail: dict[str, object]) -> dict[str, object]:
    serialized_detail = dict(detail)
    if serialized_detail.get("state") == TASK_STATUS_DONE:
        serialized_detail["state"] = "completed"

    history = serialized_detail.get("history")
    if isinstance(history, list):
        serialized_history: list[object] = []
        for entry in history:
            if isinstance(entry, dict) and entry.get("state") == TASK_STATUS_DONE:
                serialized_history.append(
                    {
                        **entry,
                        "state": "completed",
                    }
                )
            else:
                serialized_history.append(entry)
        serialized_detail["history"] = serialized_history

    return serialized_detail


class TaskCreate(BaseModel):
    task_type: ScenarioTaskType
    input: dict = Field(default_factory=dict)


class TaskControlRequest(BaseModel):
    reason: str | None = None


class TaskResponse(BaseModel):
    id: str
    workspace_id: str
    task_type: ScenarioTaskType
    status: TaskStatus
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
        recovery_state = derive_recovery_state(status=task.status, control_json=task.control_json)
        recovery_detail = build_recovery_detail(status=task.status, control_json=task.control_json)
        return cls(
            id=task.id,
            workspace_id=task.workspace_id,
            task_type=task.task_type,
            status=_serialize_task_status(task.status),
            recovery_state=_serialize_recovery_state(recovery_state),
            recovery_detail=_serialize_recovery_detail(recovery_detail),
            created_by=task.created_by,
            input_json=task.input_json,
            output_json=task.output_json,
            control_json=task.control_json,
            error_message=task.error_message,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
