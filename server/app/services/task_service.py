from pydantic import ValidationError

from app.repositories import task_repository, workspace_repository
from app.schemas.task import TaskCreate, TaskResponse
from app.services.job_assistant_service import (
    JobAssistantContractError,
    normalize_job_task_input,
    validate_job_task_contract,
)
from app.services.research_assistant_service import (
    ResearchAssistantContractError,
    normalize_research_task_input,
    validate_research_task_contract,
)
from app.services.support_copilot_service import (
    SupportCopilotContractError,
    normalize_support_task_input,
    validate_support_task_contract,
)
from app.services.task_execution_service import TaskExecutionError, enqueue_task_execution

RESEARCH_TASK_TYPES = {
    "research_summary",
    "workspace_report",
}
SUPPORT_TASK_TYPES = {
    "ticket_summary",
    "reply_draft",
}
JOB_TASK_TYPES = {
    "jd_summary",
    "resume_match",
}
SUPPORTED_TASK_TYPES = RESEARCH_TASK_TYPES | SUPPORT_TASK_TYPES | JOB_TASK_TYPES


class TaskAccessError(Exception):
    pass


class TaskValidationError(Exception):
    pass


class TaskQueueError(Exception):
    pass


def _normalize_task_input(
    *,
    workspace_module_type: str,
    task_type: str,
    input_json: dict[str, object],
) -> dict[str, object]:
    if task_type in RESEARCH_TASK_TYPES:
        validate_research_task_contract(
            workspace_module_type=workspace_module_type,
            task_type=task_type,
        )
        return normalize_research_task_input(input_json)
    if task_type in SUPPORT_TASK_TYPES:
        validate_support_task_contract(
            workspace_module_type=workspace_module_type,
            task_type=task_type,
        )
        return normalize_support_task_input(input_json)
    if task_type in JOB_TASK_TYPES:
        validate_job_task_contract(
            workspace_module_type=workspace_module_type,
            task_type=task_type,
        )
        return normalize_job_task_input(input_json)
    raise TaskValidationError(f"Unsupported task type: {task_type}")


async def create_task(
    *,
    workspace_id: str,
    user_id: str,
    payload: TaskCreate,
) -> TaskResponse:
    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        raise TaskAccessError("Workspace not found")

    if payload.task_type not in SUPPORTED_TASK_TYPES:
        raise TaskValidationError(f"Unsupported task type: {payload.task_type}")

    try:
        normalized_input = _normalize_task_input(
            workspace_module_type=workspace.module_type,
            task_type=payload.task_type,
            input_json=payload.input,
        )
    except (
        ResearchAssistantContractError,
        SupportCopilotContractError,
        JobAssistantContractError,
        ValidationError,
    ) as error:
        raise TaskValidationError(str(error)) from error

    task = task_repository.create_task(
        workspace_id=workspace_id,
        task_type=payload.task_type,
        created_by=user_id,
        input_json=normalized_input,
    )

    try:
        await enqueue_task_execution(task.id)
    except TaskExecutionError as error:
        failed_task = task_repository.update_task_status(
            task.id,
            next_status="failed",
            error_message=str(error),
        )
        if failed_task is None:
            raise TaskQueueError("Failed to enqueue task execution") from error
        raise TaskQueueError(str(error)) from error

    return TaskResponse.from_model(task)



def get_task(*, task_id: str, user_id: str) -> TaskResponse | None:
    task = task_repository.get_task_for_user(task_id, user_id)
    if task is None:
        return None
    return TaskResponse.from_model(task)



def list_workspace_tasks(*, workspace_id: str, user_id: str) -> list[TaskResponse]:
    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        raise TaskAccessError("Workspace not found")

    tasks = task_repository.list_workspace_tasks(workspace_id, user_id)
    return [TaskResponse.from_model(task) for task in tasks]
