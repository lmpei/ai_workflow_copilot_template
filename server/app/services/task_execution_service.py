from arq import create_pool

from app.core.config import get_settings
from app.core.queue import build_redis_settings
from app.models.task import TASK_STATUS_DONE, TASK_STATUS_FAILED, TASK_STATUS_RUNNING, Task
from app.repositories import task_repository

TASK_EXECUTION_JOB_NAME = "run_platform_task"


class TaskExecutionError(Exception):
    pass


def _build_placeholder_task_output(task: Task) -> dict[str, object]:
    return {
        "task_id": task.id,
        "task_type": task.task_type,
        "worker": "arq",
        "status": "completed",
    }


async def enqueue_task_execution(task_id: str) -> str:
    redis = await create_pool(build_redis_settings())
    job = await redis.enqueue_job(
        TASK_EXECUTION_JOB_NAME,
        task_id,
        _queue_name=get_settings().task_queue_name,
    )
    close = getattr(redis, "aclose", None)
    if callable(close):
        await close()
    if job is None:
        raise TaskExecutionError("Failed to enqueue task execution")
    return str(job.job_id)


def run_task_execution(task_id: str) -> dict[str, object]:
    task = task_repository.get_task(task_id)
    if task is None:
        raise TaskExecutionError("Task not found")

    task_repository.update_task_status(task.id, next_status=TASK_STATUS_RUNNING)
    try:
        output = _build_placeholder_task_output(task)
        task_repository.update_task_status(
            task.id,
            next_status=TASK_STATUS_DONE,
            output_json=output,
        )
        return output
    except Exception as error:
        task_repository.update_task_status(
            task.id,
            next_status=TASK_STATUS_FAILED,
            error_message=str(error),
        )
        raise TaskExecutionError("Task execution failed") from error
