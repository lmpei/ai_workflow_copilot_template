from arq import create_pool

from app.core.config import get_settings
from app.core.queue import build_redis_settings
from app.models.task import TASK_STATUS_DONE, TASK_STATUS_FAILED, TASK_STATUS_RUNNING, Task
from app.repositories import task_repository
from app.services.agent_service import (
    AgentAccessError,
    AgentExecutionResult,
    AgentRuntimeError,
    run_workspace_research_agent,
)

TASK_EXECUTION_JOB_NAME = "run_platform_task"
SUPPORTED_EXECUTION_TASK_TYPES = {
    "research_summary",
    "workspace_report",
}


class TaskExecutionError(Exception):
    pass


def _resolve_task_goal(task: Task) -> str:
    input_goal = task.input_json.get("goal")
    if isinstance(input_goal, str) and input_goal.strip():
        return input_goal.strip()

    if task.task_type == "workspace_report":
        return "Create a concise report for the current workspace."
    return "Summarize the most relevant findings in this workspace."


def _execute_task_agent(task: Task) -> AgentExecutionResult:
    if task.task_type not in SUPPORTED_EXECUTION_TASK_TYPES:
        raise TaskExecutionError(f"Unsupported task type: {task.task_type}")

    goal = _resolve_task_goal(task)
    return run_workspace_research_agent(
        task_id=task.id,
        workspace_id=task.workspace_id,
        user_id=task.created_by,
        goal=goal,
    )


def _build_task_output(*, task: Task, execution_result: AgentExecutionResult) -> dict[str, object]:
    return {
        "task_id": task.id,
        "task_type": task.task_type,
        "worker": "arq",
        "status": "completed",
        "agent_run_id": execution_result.agent_run_id,
        "agent_name": execution_result.agent_name,
        "result": execution_result.final_output,
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

    running_task = task_repository.update_task_status(task.id, next_status=TASK_STATUS_RUNNING)
    if running_task is None:
        raise TaskExecutionError("Task not found")

    try:
        execution_result = _execute_task_agent(running_task)
        output = _build_task_output(task=running_task, execution_result=execution_result)
        completed_task = task_repository.update_task_status(
            task.id,
            next_status=TASK_STATUS_DONE,
            output_json=output,
        )
        if completed_task is None:
            raise TaskExecutionError("Task not found")
        return output
    except (AgentRuntimeError, AgentAccessError) as error:
        failed_task = task_repository.update_task_status(
            task.id,
            next_status=TASK_STATUS_FAILED,
            error_message=str(error),
        )
        if failed_task is None:
            raise TaskExecutionError("Task not found") from error
        raise TaskExecutionError("Task execution failed") from error
    except Exception as error:
        failed_task = task_repository.update_task_status(
            task.id,
            next_status=TASK_STATUS_FAILED,
            error_message=str(error),
        )
        if failed_task is None:
            raise TaskExecutionError("Task not found") from error
        raise TaskExecutionError("Task execution failed") from error
