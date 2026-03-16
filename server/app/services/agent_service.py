from dataclasses import dataclass
from typing import Callable, Protocol

from app.agents.graph import (
    WORKSPACE_JOB_AGENT_NAME,
    WORKSPACE_RESEARCH_AGENT_NAME,
    WORKSPACE_SUPPORT_AGENT_NAME,
    build_workspace_job_graph,
    build_workspace_job_preview,
    build_workspace_research_graph,
    build_workspace_research_preview,
    build_workspace_support_graph,
    build_workspace_support_preview,
)
from app.repositories import task_repository, workspace_repository
from app.services.job_assistant_service import (
    JobAssistantContractError,
    validate_job_task_contract,
)
from app.services.research_assistant_service import (
    ResearchAssistantContractError,
    validate_research_task_contract,
)
from app.services.support_copilot_service import (
    SupportCopilotContractError,
    validate_support_task_contract,
)


class AgentAccessError(Exception):
    pass


class AgentRuntimeError(Exception):
    def __init__(self, message: str, *, agent_run_id: str | None = None) -> None:
        super().__init__(message)
        self.agent_run_id = agent_run_id


class GraphRunner(Protocol):
    def invoke(self, state: dict[str, object]) -> dict[str, object]: ...


@dataclass(frozen=True, slots=True)
class AgentExecutionResult:
    agent_run_id: str
    agent_name: str
    final_output: dict[str, object]


def _run_workspace_agent(
    *,
    task_id: str,
    workspace_id: str,
    user_id: str,
    goal: str,
    agent_name: str,
    graph_builder: Callable[[], GraphRunner],
    validate_contract: Callable[..., None],
    graph_runner: GraphRunner | None = None,
) -> AgentExecutionResult:
    task = task_repository.get_task_for_user(task_id, user_id)
    if task is None or task.workspace_id != workspace_id:
        raise AgentAccessError("Task not found")

    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        raise AgentAccessError("Workspace not found")

    try:
        validate_contract(
            workspace_module_type=workspace.module_type,
            task_type=task.task_type,
        )
    except (
        ResearchAssistantContractError,
        SupportCopilotContractError,
        JobAssistantContractError,
    ) as error:
        raise AgentRuntimeError(str(error)) from error

    agent_run = task_repository.create_agent_run(
        task_id=task_id,
        agent_name=agent_name,
    )

    try:
        running_run = task_repository.update_agent_run_status(
            agent_run.id,
            next_status="running",
        )
        if running_run is None:
            raise AgentRuntimeError("Agent run not found", agent_run_id=agent_run.id)

        graph = graph_runner or graph_builder()
        final_state = graph.invoke(
            {
                "agent_run_id": agent_run.id,
                "workspace_id": workspace_id,
                "user_id": user_id,
                "task_type": task.task_type,
                "goal": goal,
                "tool_call_ids": [],
                "documents": [],
                "matches": [],
            },
        )
        final_output = final_state.get("final_output")
        if not isinstance(final_output, dict):
            raise AgentRuntimeError(
                "Agent graph did not produce final output",
                agent_run_id=agent_run.id,
            )

        completed_run = task_repository.update_agent_run_status(
            agent_run.id,
            next_status="completed",
            final_output=final_output,
        )
        if completed_run is None:
            raise AgentRuntimeError("Agent run not found", agent_run_id=agent_run.id)

        return AgentExecutionResult(
            agent_run_id=agent_run.id,
            agent_name=agent_name,
            final_output=final_output,
        )
    except AgentRuntimeError as error:
        task_repository.update_agent_run_status(
            agent_run.id,
            next_status="failed",
            final_output={"error": str(error)},
        )
        error.agent_run_id = agent_run.id
        raise
    except Exception as error:
        task_repository.update_agent_run_status(
            agent_run.id,
            next_status="failed",
            final_output={"error": str(error)},
        )
        raise AgentRuntimeError(str(error), agent_run_id=agent_run.id) from error



def run_workspace_research_agent(
    *,
    task_id: str,
    workspace_id: str,
    user_id: str,
    goal: str,
    graph_runner: GraphRunner | None = None,
) -> AgentExecutionResult:
    return _run_workspace_agent(
        task_id=task_id,
        workspace_id=workspace_id,
        user_id=user_id,
        goal=goal,
        agent_name=WORKSPACE_RESEARCH_AGENT_NAME,
        graph_builder=build_workspace_research_graph,
        validate_contract=validate_research_task_contract,
        graph_runner=graph_runner,
    )



def run_workspace_support_agent(
    *,
    task_id: str,
    workspace_id: str,
    user_id: str,
    customer_issue: str,
    graph_runner: GraphRunner | None = None,
) -> AgentExecutionResult:
    return _run_workspace_agent(
        task_id=task_id,
        workspace_id=workspace_id,
        user_id=user_id,
        goal=customer_issue,
        agent_name=WORKSPACE_SUPPORT_AGENT_NAME,
        graph_builder=build_workspace_support_graph,
        validate_contract=validate_support_task_contract,
        graph_runner=graph_runner,
    )


def run_workspace_job_agent(
    *,
    task_id: str,
    workspace_id: str,
    user_id: str,
    target_role: str,
    graph_runner: GraphRunner | None = None,
) -> AgentExecutionResult:
    return _run_workspace_agent(
        task_id=task_id,
        workspace_id=workspace_id,
        user_id=user_id,
        goal=target_role,
        agent_name=WORKSPACE_JOB_AGENT_NAME,
        graph_builder=build_workspace_job_graph,
        validate_contract=validate_job_task_contract,
        graph_runner=graph_runner,
    )



def run_agent_preview(goal: str) -> dict[str, object]:
    return build_workspace_research_preview(goal)



def run_support_agent_preview(goal: str) -> dict[str, object]:
    return build_workspace_support_preview(goal)


def run_job_agent_preview(goal: str) -> dict[str, object]:
    return build_workspace_job_preview(goal)
