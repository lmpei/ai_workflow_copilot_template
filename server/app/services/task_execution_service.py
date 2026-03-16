from arq import create_pool

from app.core.config import get_settings
from app.core.queue import build_redis_settings
from app.models.task import TASK_STATUS_DONE, TASK_STATUS_FAILED, TASK_STATUS_RUNNING, Task
from app.repositories import task_repository, workspace_repository
from app.services.agent_service import (
    AgentAccessError,
    AgentExecutionResult,
    AgentRuntimeError,
    run_workspace_research_agent,
    run_workspace_support_agent,
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

TASK_EXECUTION_JOB_NAME = "run_platform_task"
RESEARCH_TASK_TYPES = {
    "research_summary",
    "workspace_report",
}
SUPPORT_TASK_TYPES = {
    "ticket_summary",
    "reply_draft",
}
SUPPORTED_EXECUTION_TASK_TYPES = RESEARCH_TASK_TYPES | SUPPORT_TASK_TYPES


class TaskExecutionError(Exception):
    pass


def _resolve_task_prompt(task: Task) -> str:
    if task.task_type in RESEARCH_TASK_TYPES:
        normalized_input = normalize_research_task_input(task.input_json)
        input_goal = normalized_input.get("goal")
        if isinstance(input_goal, str) and input_goal.strip():
            return input_goal.strip()

        if task.task_type == "workspace_report":
            return "Create a concise report for the current workspace."
        return "Summarize the most relevant findings in this workspace."

    if task.task_type in SUPPORT_TASK_TYPES:
        normalized_input = normalize_support_task_input(task.input_json)
        customer_issue = normalized_input.get("customer_issue")
        if isinstance(customer_issue, str) and customer_issue.strip():
            return customer_issue.strip()

        if task.task_type == "reply_draft":
            return "Draft a grounded customer reply for the current support issue."
        return "Summarize the current support issue and the best grounded next steps."

    raise TaskExecutionError(f"Unsupported task type: {task.task_type}")


def _execute_task_agent(task: Task) -> AgentExecutionResult:
    if task.task_type not in SUPPORTED_EXECUTION_TASK_TYPES:
        raise TaskExecutionError(f"Unsupported task type: {task.task_type}")

    workspace = workspace_repository.get_workspace(task.workspace_id, task.created_by)
    if workspace is None:
        raise TaskExecutionError("Workspace not found")

    prompt = _resolve_task_prompt(task)

    if task.task_type in RESEARCH_TASK_TYPES:
        try:
            validate_research_task_contract(
                workspace_module_type=workspace.module_type,
                task_type=task.task_type,
            )
        except ResearchAssistantContractError as error:
            raise TaskExecutionError(str(error)) from error

        return run_workspace_research_agent(
            task_id=task.id,
            workspace_id=task.workspace_id,
            user_id=task.created_by,
            goal=prompt,
        )

    try:
        validate_support_task_contract(
            workspace_module_type=workspace.module_type,
            task_type=task.task_type,
        )
    except SupportCopilotContractError as error:
        raise TaskExecutionError(str(error)) from error

    return run_workspace_support_agent(
        task_id=task.id,
        workspace_id=task.workspace_id,
        user_id=task.created_by,
        customer_issue=prompt,
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
    except TaskExecutionError as error:
        failed_task = task_repository.update_task_status(
            task.id,
            next_status=TASK_STATUS_FAILED,
            error_message=str(error),
        )
        if failed_task is None:
            raise TaskExecutionError("Task not found") from error
        raise
    except (
        AgentRuntimeError,
        AgentAccessError,
        ResearchAssistantContractError,
        SupportCopilotContractError,
    ) as error:
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
