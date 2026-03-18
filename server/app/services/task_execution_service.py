from arq import create_pool

from app.core.config import get_settings
from app.core.queue import build_redis_settings
from app.models.task import (
    TASK_STATUS_DONE,
    TASK_STATUS_FAILED,
    TASK_STATUS_PENDING,
    TASK_STATUS_RUNNING,
    Task,
)
from app.repositories import task_repository, workspace_repository
from app.services.agent_service import (
    AgentAccessError,
    AgentExecutionResult,
    AgentRuntimeError,
    run_workspace_job_agent,
    run_workspace_research_agent,
    run_workspace_support_agent,
)
from app.services.job_assistant_service import (
    JobAssistantContractError,
    normalize_job_task_input,
    validate_job_task_contract,
)
from app.services.research_assistant_service import (
    ResearchAssistantContractError,
    build_research_task_search_query,
    resolve_research_task_input,
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
JOB_TASK_TYPES = {
    "jd_summary",
    "resume_match",
}
SUPPORTED_EXECUTION_TASK_TYPES = RESEARCH_TASK_TYPES | SUPPORT_TASK_TYPES | JOB_TASK_TYPES


class TaskExecutionError(Exception):
    pass


def _resolve_task_prompt(task: Task) -> str:
    if task.task_type in RESEARCH_TASK_TYPES:
        research_input = resolve_research_task_input(
            task_type=task.task_type,
            input_json=task.input_json,
        )
        return build_research_task_search_query(
            task_type=task.task_type,
            research_input=research_input,
        )

    if task.task_type in SUPPORT_TASK_TYPES:
        normalized_input = normalize_support_task_input(task.input_json)
        customer_issue = normalized_input.get("customer_issue")
        if isinstance(customer_issue, str) and customer_issue.strip():
            return customer_issue.strip()

        if task.task_type == "reply_draft":
            return "Draft a grounded customer reply for the current support issue."
        return "Summarize the current support issue and the best grounded next steps."

    if task.task_type in JOB_TASK_TYPES:
        normalized_input = normalize_job_task_input(task.input_json)
        target_role = normalized_input.get("target_role")
        if isinstance(target_role, str) and target_role.strip():
            return target_role.strip()

        if task.task_type == "resume_match":
            return "Assess fit between the indexed hiring materials and the target role."
        return "Summarize the key role requirements from the indexed job materials."

    raise TaskExecutionError(f"Unsupported task type: {task.task_type}")


def _execute_task_agent(task: Task) -> AgentExecutionResult:
    if task.task_type not in SUPPORTED_EXECUTION_TASK_TYPES:
        raise TaskExecutionError(f"Unsupported task type: {task.task_type}")

    workspace = workspace_repository.get_workspace(task.workspace_id, task.created_by)
    if workspace is None:
        raise TaskExecutionError("Workspace not found")

    if task.task_type in RESEARCH_TASK_TYPES:
        try:
            validate_research_task_contract(
                workspace_module_type=workspace.module_type,
                task_type=task.task_type,
            )
        except ResearchAssistantContractError as error:
            raise TaskExecutionError(str(error)) from error

        research_input = resolve_research_task_input(
            task_type=task.task_type,
            input_json=task.input_json,
        )
        prompt = build_research_task_search_query(
            task_type=task.task_type,
            research_input=research_input,
        )

        return run_workspace_research_agent(
            task_id=task.id,
            workspace_id=task.workspace_id,
            user_id=task.created_by,
            goal=prompt,
            research_input=research_input.model_dump(exclude_none=True),
        )

    if task.task_type in SUPPORT_TASK_TYPES:
        prompt = _resolve_task_prompt(task)
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

    prompt = _resolve_task_prompt(task)
    try:
        validate_job_task_contract(
            workspace_module_type=workspace.module_type,
            task_type=task.task_type,
        )
    except JobAssistantContractError as error:
        raise TaskExecutionError(str(error)) from error

    return run_workspace_job_agent(
        task_id=task.id,
        workspace_id=task.workspace_id,
        user_id=task.created_by,
        target_role=prompt,
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


def _build_task_state_snapshot(task: Task) -> dict[str, object]:
    if task.status == TASK_STATUS_DONE and task.output_json:
        return dict(task.output_json)

    snapshot: dict[str, object] = {
        "task_id": task.id,
        "task_type": task.task_type,
        "worker": "arq",
        "status": task.status,
        "skipped": True,
    }
    if task.error_message:
        snapshot["error_message"] = task.error_message
    return snapshot


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

    if task.status != TASK_STATUS_PENDING:
        return _build_task_state_snapshot(task)

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
        JobAssistantContractError,
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
