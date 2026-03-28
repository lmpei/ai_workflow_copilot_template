"""Explicit task-execution extensions for module-specific runtime behavior.

The generic task executor should stop at lifecycle boundaries. Anything that is
specific to one module, such as Research lineage resolution, Research trace
records, or Support case synchronization, lives here.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol, cast

from app.models.task import TASK_STATUS_DONE, Task
from app.repositories import task_repository
from app.schemas.research import ResearchLineage, ResearchTaskInput, ResearchTaskType
from app.schemas.scenario import (
    MODULE_TYPE_RESEARCH,
    MODULE_TYPE_SUPPORT,
    get_scenario_task_module_type,
)
from app.services import research_asset_service, support_case_service, trace_service
from app.services.agent_service import AgentExecutionResult
from app.services.research_assistant_service import (
    ResearchAssistantContractError,
    build_research_task_search_query,
    resolve_research_task_input,
)

RESEARCH_TASK_TRACE_TYPE = "research_task"


class TaskExecutionExtensionError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class TaskExecutionExtensionArtifacts:
    trace_request: dict[str, object] | None = None


class TaskExecutionExtension(Protocol):
    def prepare(self, *, task: Task) -> TaskExecutionExtensionArtifacts: ...

    def enrich_execution_result(
        self,
        *,
        task: Task,
        execution_result: AgentExecutionResult,
    ) -> None: ...

    def enrich_completed_output(
        self,
        *,
        task: Task,
        execution_result: AgentExecutionResult,
        output_json: dict[str, object],
        artifacts: TaskExecutionExtensionArtifacts,
        started_at: datetime,
    ) -> None: ...

    def build_failed_output(
        self,
        *,
        task: Task,
        error: Exception,
        failure: dict[str, object],
        artifacts: TaskExecutionExtensionArtifacts,
        started_at: datetime,
    ) -> dict[str, object] | None: ...


class NoopTaskExecutionExtension:
    """Default extension for modules that do not add runtime side effects."""

    def prepare(self, *, task: Task) -> TaskExecutionExtensionArtifacts:
        return TaskExecutionExtensionArtifacts()

    def enrich_execution_result(
        self,
        *,
        task: Task,
        execution_result: AgentExecutionResult,
    ) -> None:
        return None

    def enrich_completed_output(
        self,
        *,
        task: Task,
        execution_result: AgentExecutionResult,
        output_json: dict[str, object],
        artifacts: TaskExecutionExtensionArtifacts,
        started_at: datetime,
    ) -> None:
        return None

    def build_failed_output(
        self,
        *,
        task: Task,
        error: Exception,
        failure: dict[str, object],
        artifacts: TaskExecutionExtensionArtifacts,
        started_at: datetime,
    ) -> dict[str, object] | None:
        return None


def resolve_research_task_lineage(
    *,
    task: Task,
    research_input: ResearchTaskInput,
) -> ResearchLineage | None:
    if not research_input.parent_task_id:
        return None

    parent_task = task_repository.get_task(research_input.parent_task_id)
    if parent_task is None or parent_task.workspace_id != task.workspace_id:
        raise TaskExecutionExtensionError("Parent research task not found in this workspace")
    if get_scenario_task_module_type(parent_task.task_type) != MODULE_TYPE_RESEARCH:
        raise TaskExecutionExtensionError("Parent task must be a completed Research task")
    if parent_task.status != TASK_STATUS_DONE:
        raise TaskExecutionExtensionError("Parent research task must be completed before follow-up")

    result = parent_task.output_json.get("result")
    if not isinstance(result, dict) or result.get("module_type") != MODULE_TYPE_RESEARCH:
        raise TaskExecutionExtensionError("Parent research task does not contain a structured Research result")

    title = result.get("title")
    summary = result.get("summary")
    if not isinstance(title, str) or not title.strip():
        raise TaskExecutionExtensionError("Parent research task is missing a Research title")
    if not isinstance(summary, str) or not summary.strip():
        raise TaskExecutionExtensionError("Parent research task is missing a Research summary")

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
        parent_task_type=cast(ResearchTaskType, parent_task.task_type),
        parent_title=title.strip(),
        parent_goal=parent_goal,
        parent_summary=summary.strip(),
        parent_report_headline=parent_report_headline,
        continuation_notes=research_input.continuation_notes,
    )


def _build_research_trace_request(task: Task) -> dict[str, object]:
    request_json: dict[str, object] = {
        "task_type": task.task_type,
        "input": dict(task.input_json),
    }
    research_task_type = cast(ResearchTaskType, task.task_type)
    try:
        research_input = resolve_research_task_input(
            task_type=research_task_type,
            input_json=task.input_json,
        )
    except ResearchAssistantContractError:
        return request_json

    research_lineage = resolve_research_task_lineage(
        task=task,
        research_input=research_input,
    )

    request_json["normalized_input"] = research_input.model_dump(exclude_none=True)
    if research_lineage is not None:
        request_json["lineage"] = research_lineage.model_dump(exclude_none=True)
    request_json["prompt"] = build_research_task_search_query(
        task_type=research_task_type,
        research_input=research_input,
        lineage=research_lineage,
    )
    return request_json


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


class ResearchTaskExecutionExtension:
    """Research-only execution hooks layered on top of the generic executor."""

    def prepare(self, *, task: Task) -> TaskExecutionExtensionArtifacts:
        return TaskExecutionExtensionArtifacts(trace_request=_build_research_trace_request(task))

    def enrich_execution_result(
        self,
        *,
        task: Task,
        execution_result: AgentExecutionResult,
    ) -> None:
        research_asset_id = task.input_json.get("research_asset_id")
        if not isinstance(research_asset_id, str) or not research_asset_id:
            return

        try:
            asset_metadata = research_asset_service.sync_research_asset_from_task(
                research_asset_id=research_asset_id,
                task=task,
                result_json=execution_result.final_output,
            )
        except Exception as error:
            raise TaskExecutionExtensionError(str(error)) from error

        result_metadata = execution_result.final_output.get("metadata")
        if not isinstance(result_metadata, dict):
            result_metadata = {}
            execution_result.final_output["metadata"] = result_metadata
        result_metadata.update(asset_metadata)

    def enrich_completed_output(
        self,
        *,
        task: Task,
        execution_result: AgentExecutionResult,
        output_json: dict[str, object],
        artifacts: TaskExecutionExtensionArtifacts,
        started_at: datetime,
    ) -> None:
        if artifacts.trace_request is None:
            return

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
            task=task,
            request_json=artifacts.trace_request,
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
                "module_type": execution_result.final_output.get("module_type", MODULE_TYPE_RESEARCH),
                "task_type": execution_result.final_output.get("task_type", task.task_type),
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
            output_json["trace_id"] = trace_id

    def build_failed_output(
        self,
        *,
        task: Task,
        error: Exception,
        failure: dict[str, object],
        artifacts: TaskExecutionExtensionArtifacts,
        started_at: datetime,
    ) -> dict[str, object] | None:
        if artifacts.trace_request is None:
            return None

        latency_ms = max(int((datetime.now(UTC) - started_at).total_seconds() * 1000), 0)
        trace_id = _record_research_task_trace(
            task=task,
            request_json=artifacts.trace_request,
            response_json={
                "status": "failed",
                "error": str(error),
                "failure": failure,
            },
            metadata_json={
                "module_type": MODULE_TYPE_RESEARCH,
                "task_type": task.task_type,
                "failure": failure,
            },
            latency_ms=latency_ms,
            error_message=str(error),
            agent_run_id=getattr(error, "agent_run_id", None),
        )
        return _build_failed_task_output(
            task=task,
            error_message=str(error),
            failure=failure,
            trace_id=trace_id,
        )


class SupportTaskExecutionExtension(NoopTaskExecutionExtension):
    """Support-only hooks that sync completed runs into the persistent case workbench."""

    def enrich_execution_result(
        self,
        *,
        task: Task,
        execution_result: AgentExecutionResult,
    ) -> None:
        try:
            case_metadata = support_case_service.sync_support_case_from_task(
                task=task,
                result_json=execution_result.final_output,
            )
        except Exception as error:
            raise TaskExecutionExtensionError(str(error)) from error

        result_metadata = execution_result.final_output.get("metadata")
        if not isinstance(result_metadata, dict):
            result_metadata = {}
            execution_result.final_output["metadata"] = result_metadata
        result_metadata.update(case_metadata)


_NOOP_TASK_EXECUTION_EXTENSION = NoopTaskExecutionExtension()
_RESEARCH_TASK_EXECUTION_EXTENSION = ResearchTaskExecutionExtension()
_SUPPORT_TASK_EXECUTION_EXTENSION = SupportTaskExecutionExtension()


def get_task_execution_extension(module_type: str) -> TaskExecutionExtension:
    if module_type == MODULE_TYPE_RESEARCH:
        return _RESEARCH_TASK_EXECUTION_EXTENSION
    if module_type == MODULE_TYPE_SUPPORT:
        return _SUPPORT_TASK_EXECUTION_EXTENSION
    return _NOOP_TASK_EXECUTION_EXTENSION
