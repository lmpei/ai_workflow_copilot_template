from arq import create_pool

from datetime import UTC, datetime

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
from app.services import trace_service
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
    ResearchLineage,
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
RESEARCH_TASK_TRACE_TYPE = "research_task"
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
        research_lineage = _resolve_research_lineage(
            task=task,
            research_input=research_input,
        )
        prompt = build_research_task_search_query(
            task_type=task.task_type,
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
    if task.output_json:
        snapshot = dict(task.output_json)
        if task.error_message and "error_message" not in snapshot:
            snapshot["error_message"] = task.error_message
        return snapshot

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


def _build_research_trace_request(task: Task) -> dict[str, object]:
    request_json: dict[str, object] = {
        "task_type": task.task_type,
        "input": dict(task.input_json),
    }
    try:
        research_input = resolve_research_task_input(
            task_type=task.task_type,
            input_json=task.input_json,
        )
    except ResearchAssistantContractError:
        return request_json

    research_lineage = _resolve_research_lineage(
        task=task,
        research_input=research_input,
    )

    request_json["normalized_input"] = research_input.model_dump(exclude_none=True)
    if research_lineage is not None:
        request_json["lineage"] = research_lineage.model_dump(exclude_none=True)
    request_json["prompt"] = build_research_task_search_query(
        task_type=task.task_type,
        research_input=research_input,
        lineage=research_lineage,
    )
    return request_json


def _resolve_research_lineage(
    *,
    task: Task,
    research_input,
) -> ResearchLineage | None:
    if not research_input.parent_task_id:
        return None

    parent_task = task_repository.get_task(research_input.parent_task_id)
    if parent_task is None or parent_task.workspace_id != task.workspace_id:
        raise TaskExecutionError("Parent research task not found in this workspace")
    if parent_task.task_type not in RESEARCH_TASK_TYPES:
        raise TaskExecutionError("Parent task must be a completed Research task")
    if parent_task.status != TASK_STATUS_DONE:
        raise TaskExecutionError("Parent research task must be completed before follow-up")

    result = parent_task.output_json.get("result")
    if not isinstance(result, dict) or result.get("module_type") != "research":
        raise TaskExecutionError("Parent research task does not contain a structured Research result")

    title = result.get("title")
    summary = result.get("summary")
    if not isinstance(title, str) or not title.strip():
        raise TaskExecutionError("Parent research task is missing a Research title")
    if not isinstance(summary, str) or not summary.strip():
        raise TaskExecutionError("Parent research task is missing a Research summary")

    parent_input = result.get("input")
    parent_goal: str | None = None
    if isinstance(parent_input, dict):
        raw_parent_goal = parent_input.get("goal")
        if isinstance(raw_parent_goal, str) and raw_parent_goal.strip():
            parent_goal = raw_parent_goal.strip()

    parent_report = result.get("report")
    parent_report_headline: str | None = None
    if isinstance(parent_report, dict):
        raw_headline = parent_report.get("headline")
        if isinstance(raw_headline, str) and raw_headline.strip():
            parent_report_headline = raw_headline.strip()

    return ResearchLineage(
        parent_task_id=parent_task.id,
        parent_task_type=parent_task.task_type,
        parent_title=title.strip(),
        parent_goal=parent_goal,
        parent_summary=summary.strip(),
        parent_report_headline=parent_report_headline,
        continuation_notes=research_input.continuation_notes,
    )


def _classify_task_failure(error: Exception) -> dict[str, object]:
    if isinstance(error, (ResearchAssistantContractError, SupportCopilotContractError, JobAssistantContractError)):
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
        if isinstance(
            error.__cause__,
            (ResearchAssistantContractError, SupportCopilotContractError, JobAssistantContractError),
        ):
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
    return {
        "type": "unexpected_error",
        "stage": "unexpected",
        "retryable": False,
    }


def _record_research_task_trace(
    *,
    task: Task,
    request_json: dict[str, object],
    response_json: dict[str, object],
    metadata_json: dict[str, object],
    latency_ms: int,
    error_message: str | None = None,
    agent_run_id: str | None = None,
) -> str | None:
    try:
        return trace_service.record_trace(
            workspace_id=task.workspace_id,
            task_id=task.id,
            agent_run_id=agent_run_id,
            trace_type=RESEARCH_TASK_TRACE_TYPE,
            request_json=request_json,
            response_json=response_json,
            metadata_json=metadata_json,
            error_message=error_message,
            latency_ms=latency_ms,
        )
    except Exception:
        return None


def _build_failed_task_output(
    *,
    task: Task,
    error_message: str,
    failure: dict[str, object],
    trace_id: str | None,
) -> dict[str, object]:
    output: dict[str, object] = {
        "task_id": task.id,
        "task_type": task.task_type,
        "worker": "arq",
        "status": "failed",
        "error": {
            "message": error_message,
            **failure,
        },
    }
    if trace_id:
        output["trace_id"] = trace_id
    return output


def _mark_task_failed(
    *,
    task: Task,
    error: Exception,
    research_trace_request: dict[str, object] | None,
    started_at: datetime,
) -> Task | None:
    failure = _classify_task_failure(error)
    trace_id: str | None = None
    output_json: dict[str, object] | None = None

    if research_trace_request is not None:
        latency_ms = max(int((datetime.now(UTC) - started_at).total_seconds() * 1000), 0)
        trace_id = _record_research_task_trace(
            task=task,
            request_json=research_trace_request,
            response_json={
                "status": "failed",
                "error": str(error),
                "failure": failure,
            },
            metadata_json={
                "module_type": "research",
                "task_type": task.task_type,
                "failure": failure,
            },
            latency_ms=latency_ms,
            error_message=str(error),
            agent_run_id=getattr(error, "agent_run_id", None),
        )
        output_json = _build_failed_task_output(
            task=task,
            error_message=str(error),
            failure=failure,
            trace_id=trace_id,
        )

    return task_repository.update_task_status(
        task.id,
        next_status=TASK_STATUS_FAILED,
        error_message=str(error),
        output_json=output_json,
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

    if task.status != TASK_STATUS_PENDING:
        return _build_task_state_snapshot(task)

    running_task = task_repository.update_task_status(task.id, next_status=TASK_STATUS_RUNNING)
    if running_task is None:
        raise TaskExecutionError("Task not found")

    started_at = datetime.now(UTC)
    research_trace_request = (
        _build_research_trace_request(running_task)
        if running_task.task_type in RESEARCH_TASK_TYPES
        else None
    )

    try:
        execution_result = _execute_task_agent(running_task)
        output = _build_task_output(task=running_task, execution_result=execution_result)
        if research_trace_request is not None:
            latency_ms = max(int((datetime.now(UTC) - started_at).total_seconds() * 1000), 0)
            result_metadata = execution_result.final_output.get("metadata", {})
            if not isinstance(result_metadata, dict):
                result_metadata = {}
            trust_metadata = result_metadata.get("trust", {})
            if not isinstance(trust_metadata, dict):
                trust_metadata = {}
            regression_baseline = result_metadata.get("regression_baseline", {})
            if not isinstance(regression_baseline, dict):
                regression_baseline = {}

            trace_id = _record_research_task_trace(
                task=running_task,
                request_json=research_trace_request,
                response_json={
                    "status": "completed",
                    "title": execution_result.final_output.get("title"),
                    "summary": execution_result.final_output.get("summary"),
                    "report_ready": result_metadata.get("report_ready"),
                    "evidence_status": result_metadata.get("evidence_status"),
                    "regression_passed": result_metadata.get("regression_passed"),
                    "regression_baseline": regression_baseline,
                    "trust": trust_metadata,
                    "error": None,
                },
                metadata_json={
                    "module_type": execution_result.final_output.get("module_type", "research"),
                    "task_type": execution_result.final_output.get("task_type", running_task.task_type),
                    "deliverable": result_metadata.get("deliverable"),
                    "requested_sections": result_metadata.get("requested_sections", []),
                    "is_follow_up": result_metadata.get("is_follow_up"),
                    "parent_task_id": result_metadata.get("parent_task_id"),
                    "report_ready": result_metadata.get("report_ready"),
                    "evidence_status": result_metadata.get("evidence_status"),
                    "regression_passed": result_metadata.get("regression_passed"),
                    "regression_baseline": regression_baseline,
                    "trust": trust_metadata,
                },
                latency_ms=latency_ms,
                agent_run_id=execution_result.agent_run_id,
            )
            if trace_id is not None:
                output["trace_id"] = trace_id

        completed_task = task_repository.update_task_status(
            task.id,
            next_status=TASK_STATUS_DONE,
            output_json=output,
        )
        if completed_task is None:
            raise TaskExecutionError("Task not found")
        return output
    except TaskExecutionError as error:
        failed_task = _mark_task_failed(
            task=running_task,
            error=error,
            research_trace_request=research_trace_request,
            started_at=started_at,
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
        failed_task = _mark_task_failed(
            task=running_task,
            error=error,
            research_trace_request=research_trace_request,
            started_at=started_at,
        )
        if failed_task is None:
            raise TaskExecutionError("Task not found") from error
        raise TaskExecutionError("Task execution failed") from error
    except Exception as error:
        failed_task = _mark_task_failed(
            task=running_task,
            error=error,
            research_trace_request=research_trace_request,
            started_at=started_at,
        )
        if failed_task is None:
            raise TaskExecutionError("Task not found") from error
        raise TaskExecutionError("Task execution failed") from error
