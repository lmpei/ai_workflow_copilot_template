from dataclasses import dataclass
from typing import Protocol

from app.agents.graph import (
    WORKSPACE_RESEARCH_AGENT_NAME,
    build_workspace_research_graph,
    build_workspace_research_preview,
)
from app.repositories import task_repository, workspace_repository
from app.services.research_assistant_service import (
    ResearchAssistantContractError,
    validate_research_task_contract,
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


def run_workspace_research_agent(
    *,
    task_id: str,
    workspace_id: str,
    user_id: str,
    goal: str,
    graph_runner: GraphRunner | None = None,
) -> AgentExecutionResult:
    task = task_repository.get_task_for_user(task_id, user_id)
    if task is None or task.workspace_id != workspace_id:
        raise AgentAccessError("Task not found")

    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        raise AgentAccessError("Workspace not found")

    try:
        validate_research_task_contract(
            workspace_module_type=workspace.module_type,
            task_type=task.task_type,
        )
    except ResearchAssistantContractError as error:
        raise AgentRuntimeError(str(error)) from error

    agent_run = task_repository.create_agent_run(
        task_id=task_id,
        agent_name=WORKSPACE_RESEARCH_AGENT_NAME,
    )

    try:
        running_run = task_repository.update_agent_run_status(
            agent_run.id,
            next_status="running",
        )
        if running_run is None:
            raise AgentRuntimeError("Agent run not found", agent_run_id=agent_run.id)

        graph = graph_runner or build_workspace_research_graph()
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
            agent_name=WORKSPACE_RESEARCH_AGENT_NAME,
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


def run_agent_preview(goal: str) -> dict[str, object]:
    return build_workspace_research_preview(goal)
