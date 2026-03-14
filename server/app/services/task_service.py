from app.repositories import task_repository, workspace_repository
from app.schemas.task import TaskCreate, TaskResponse
from app.services.task_execution_service import TaskExecutionError, enqueue_task_execution

SUPPORTED_TASK_TYPES = {
    "research_summary",
    "workspace_report",
}


class TaskAccessError(Exception):
    pass


class TaskValidationError(Exception):
    pass


class TaskQueueError(Exception):
    pass


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

    task = task_repository.create_task(
        workspace_id=workspace_id,
        task_type=payload.task_type,
        created_by=user_id,
        input_json=payload.input,
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
