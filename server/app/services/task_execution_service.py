"""Generic task lifecycle executor.

This service owns the shared pending -> running -> completed or failed flow.
Module-specific tracing, lineage, and asset behavior should enter only through
task execution extensions.
"""

from datetime import UTC, datetime
from typing import cast

from arq import create_pool

from app.core.config import get_settings
from app.core.queue import build_redis_settings
from app.core.runtime_control import (
    build_cancelled_control_from_request,
    derive_recovery_state,
    is_cancel_requested,
)
from app.models.task import (
    TASK_STATUS_DONE,
    TASK_STATUS_FAILED,
    TASK_STATUS_PENDING,
    TASK_STATUS_RUNNING,
    Task,
)
from app.repositories import task_repository, workspace_repository
from app.schemas.research import ResearchTaskType
from app.schemas.scenario import (
    MODULE_TYPE_JOB,
    MODULE_TYPE_RESEARCH,
    MODULE_TYPE_SUPPORT,
    get_scenario_task_module_type,
)
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
    build_support_task_search_query,
    resolve_support_task_input,
    validate_support_task_contract,
)
from app.services.task_execution_extensions import (
    TaskExecutionExtensionArtifacts,
    TaskExecutionExtensionError,
    get_task_execution_extension,
    resolve_research_task_lineage,
)

TASK_EXECUTION_JOB_NAME = "run_platform_task"
MODULE_CONTRACT_VALIDATORS = {
    MODULE_TYPE_RESEARCH: validate_research_task_contract,
    MODULE_TYPE_SUPPORT: validate_support_task_contract,
    MODULE_TYPE_JOB: validate_job_task_contract,
}
MODULE_CONTRACT_ERRORS = (
    ResearchAssistantContractError,
    SupportCopilotContractError,
    JobAssistantContractError,
)


class TaskExecutionError(Exception):
    pass


class TaskControlActionError(TaskExecutionError):
    def __init__(self, *, action: str, message: str) -> None:
        super().__init__(message)
        self.action = action


def _resolve_task_module_type(task_type: str) -> str:
    try:
        return get_scenario_task_module_type(task_type)
    except ValueError as error:
        raise TaskExecutionError(str(error)) from error


def _coerce_research_task_type(task_type: str) -> ResearchTaskType:
    if task_type in {"research_summary", "workspace_report"}:
        return cast(ResearchTaskType, task_type)
    raise TaskExecutionError(f"Unsupported Research task type: {task_type}")


def _resolve_task_prompt(task: Task) -> str:
    task_module_type = _resolve_task_module_type(task.task_type)
    if task_module_type == MODULE_TYPE_RESEARCH:
        research_task_type = _coerce_research_task_type(task.task_type)
        research_input = resolve_research_task_input(
            task_type=research_task_type,
            input_json=task.input_json,
        )
        return build_research_task_search_query(
            task_type=research_task_type,
            research_input=research_input,
        )

    if task_module_type == MODULE_TYPE_SUPPORT:
        support_input = resolve_support_task_input(task.input_json)
        support_query = build_support_task_search_query(support_input)
        if support_query:
            return support_query

        if task.task_type == "reply_draft":
            return "Draft a grounded customer reply for the current support issue."
        return "Summarize the current support issue and the best grounded next steps."

    normalized_input = normalize_job_task_input(task.input_json)
    target_role = normalized_input.get("target_role")
    if isinstance(target_role, str) and target_role.strip():
        return target_role.strip()

    if task.task_type == "resume_match":
        return "Assess fit between the indexed hiring materials and the target role."
    return "Summarize the key role requirements from the indexed job materials."


def _execute_task_agent(task: Task) -> AgentExecutionResult:
    task_module_type = _resolve_task_module_type(task.task_type)

    workspace = workspace_repository.get_workspace(task.workspace_id, task.created_by)
    if workspace is None:
        raise TaskExecutionError("Workspace not found")

    validate_contract = MODULE_CONTRACT_VALIDATORS[task_module_type]
    try:
        validate_contract(
            workspace_module_type=workspace.module_type,
            task_type=task.task_type,
        )
    except MODULE_CONTRACT_ERRORS as error:
        raise TaskExecutionError(str(error)) from error

    if task_module_type == MODULE_TYPE_RESEARCH:
        research_task_type = _coerce_research_task_type(task.task_type)
        research_input = resolve_research_task_input(
            task_type=research_task_type,
            input_json=task.input_json,
        )
        research_lineage = resolve_research_task_lineage(
            task=task,
            research_input=research_input,
        )
        prompt = build_research_task_search_query(
            task_type=research_task_type,
            research_input=research_input,
            lineage=research_lineage,
        )

        return run_workspace_research_agent(
            task_id=task.id,
            workspace_id=task.workspace_id,
            user_id=task.created_by,
            goal=prompt,
            research_input=research_input.model_dump(exclude_none=True),
            research_lineage=research_lineage.model_dump(exclude_none=True) if research_lineage is not None else None,
        )

    prompt = _resolve_task_prompt(task)
    if task_module_type == MODULE_TYPE_SUPPORT:
        support_input = resolve_support_task_input(task.input_json)
        return run_workspace_support_agent(
            task_id=task.id,
            workspace_id=task.workspace_id,
            user_id=task.created_by,
            customer_issue=prompt,
            support_input=support_input.model_dump(exclude_none=True),
        )

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
    if task.output_json:
        snapshot = dict(task.output_json)
        if task.error_message and "error_message" not in snapshot:
            snapshot["error_message"] = task.error_message
    else:
        snapshot = {
            "task_id": task.id,
            "task_type": task.task_type,
            "worker": "arq",
            "status": task.status,
            "skipped": True,
        }
        if task.error_message:
            snapshot["error_message"] = task.error_message

    snapshot["control_json"] = task.control_json
    snapshot["recovery_state"] = derive_recovery_state(
        status=task.status,
        control_json=task.control_json,
    )
    return snapshot


def _classify_task_failure(error: Exception) -> dict[str, object]:
    if isinstance(error, TaskControlActionError):
        return {
            "type": "control_action",
            "stage": "operator_control",
            "retryable": True,
            "action": error.action,
        }
    if isinstance(error, MODULE_CONTRACT_ERRORS):
        return {
            "type": "contract_error",
            "stage": "validation",
            "retryable": False,
        }
    if isinstance(error, AgentAccessError):
        return {
            "type": "agent_access_error",
            "stage": "agent_access",
            "retryable": False,
        }
    if isinstance(error, AgentRuntimeError):
        return {
            "type": "agent_runtime_error",
            "stage": "agent_execution",
            "retryable": False,
        }
    if isinstance(error, TaskExecutionError):
        if isinstance(error.__cause__, MODULE_CONTRACT_ERRORS):
            return {
                "type": "contract_error",
                "stage": "validation",
                "retryable": False,
            }
        return {
            "type": "task_execution_error",
            "stage": "task_execution",
            "retryable": False,
        }
    if isinstance(error, TaskExecutionExtensionError):
        return {
            "type": "task_execution_error",
            "stage": "task_execution_extension",
            "retryable": False,
        }
    return {
        "type": "unexpected_error",
        "stage": "unexpected",
        "retryable": False,
    }


def _mark_task_failed(
    *,
    task: Task,
    error: Exception,
    execution_extension,
    extension_artifacts: TaskExecutionExtensionArtifacts,
    started_at: datetime,
    control_json: dict[str, object] | None = None,
) -> Task | None:
    failure = _classify_task_failure(error)
    output_json = execution_extension.build_failed_output(
        task=task,
        error=error,
        failure=failure,
        artifacts=extension_artifacts,
        started_at=started_at,
    )

    return task_repository.update_task_status(
        task.id,
        next_status=TASK_STATUS_FAILED,
        error_message=str(error),
        output_json=output_json,
        control_json=control_json,
    )


def _cancel_task_from_control_request(task: Task) -> Task | None:
    return task_repository.update_task_status(
        task.id,
        next_status=TASK_STATUS_FAILED,
        error_message="Task cancelled by operator",
        control_json=build_cancelled_control_from_request(
            current_status=task.status,
            current_control_json=task.control_json,
            fallback_user_id=task.created_by,
        ),
    )


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

    if is_cancel_requested(task.control_json):
        cancelled_task = _cancel_task_from_control_request(task)
        if cancelled_task is None:
            raise TaskExecutionError("Task not found")
        return _build_task_state_snapshot(cancelled_task)

    if task.status != TASK_STATUS_PENDING:
        return _build_task_state_snapshot(task)

    running_task = task_repository.update_task_status(task.id, next_status=TASK_STATUS_RUNNING)
    if running_task is None:
        raise TaskExecutionError("Task not found")

    started_at = datetime.now(UTC)
    # The generic executor only manages lifecycle and control boundaries.
    # Module-specific side effects are delegated to explicit extensions.
    execution_extension = get_task_execution_extension(
        _resolve_task_module_type(running_task.task_type),
    )
    extension_artifacts = TaskExecutionExtensionArtifacts()

    try:
        extension_artifacts = execution_extension.prepare(task=running_task)
        execution_result = _execute_task_agent(running_task)
        execution_extension.enrich_execution_result(
            task=running_task,
            execution_result=execution_result,
        )
        refreshed_running_task = task_repository.get_task(task.id)
        if refreshed_running_task is None:
            raise TaskExecutionError("Task not found")
        if is_cancel_requested(refreshed_running_task.control_json):
            cancelled_error = TaskControlActionError(
                action="cancel",
                message="Task cancelled by operator",
            )
            failed_task = _mark_task_failed(
                task=refreshed_running_task,
                error=cancelled_error,
                execution_extension=execution_extension,
                extension_artifacts=extension_artifacts,
                started_at=started_at,
                control_json=build_cancelled_control_from_request(
                    current_status=refreshed_running_task.status,
                    current_control_json=refreshed_running_task.control_json,
                    fallback_user_id=refreshed_running_task.created_by,
                ),
            )
            if failed_task is None:
                raise TaskExecutionError("Task not found")
            return _build_task_state_snapshot(failed_task)

        output = _build_task_output(task=running_task, execution_result=execution_result)
        execution_extension.enrich_completed_output(
            task=running_task,
            execution_result=execution_result,
            output_json=output,
            artifacts=extension_artifacts,
            started_at=started_at,
        )

        completed_task = task_repository.update_task_status(
            task.id,
            next_status=TASK_STATUS_DONE,
            output_json=output,
        )
        if completed_task is None:
            raise TaskExecutionError("Task not found")
        return _build_task_state_snapshot(completed_task)
    except TaskExecutionError as error:
        failed_task = _mark_task_failed(
            task=running_task,
            error=error,
            execution_extension=execution_extension,
            extension_artifacts=extension_artifacts,
            started_at=started_at,
        )
        if failed_task is None:
            raise TaskExecutionError("Task not found") from error
        raise
    except TaskExecutionExtensionError as error:
        failed_task = _mark_task_failed(
            task=running_task,
            error=error,
            execution_extension=execution_extension,
            extension_artifacts=extension_artifacts,
            started_at=started_at,
        )
        if failed_task is None:
            raise TaskExecutionError("Task not found") from error
        raise TaskExecutionError(str(error)) from error
    except (
        AgentRuntimeError,
        AgentAccessError,
        ResearchAssistantContractError,
        SupportCopilotContractError,
        JobAssistantContractError,
    ) as error:
        failed_task = _mark_task_failed(
            task=running_task,
            error=error,
            execution_extension=execution_extension,
            extension_artifacts=extension_artifacts,
            started_at=started_at,
        )
        if failed_task is None:
            raise TaskExecutionError("Task not found") from error
        raise TaskExecutionError("Task execution failed") from error
    except Exception as error:
        failed_task = _mark_task_failed(
            task=running_task,
            error=error,
            execution_extension=execution_extension,
            extension_artifacts=extension_artifacts,
            started_at=started_at,
        )
        if failed_task is None:
            raise TaskExecutionError("Task not found") from error
        raise TaskExecutionError("Task execution failed") from error
