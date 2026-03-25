"""Workspace agent graphs built from one shared execution skeleton."""

from typing import Any, TypedDict, cast

from langgraph.graph import END, START, StateGraph

from app.agents.tool_registry import invoke_tool
from app.schemas.job import JobTaskType
from app.schemas.research import ResearchTaskType
from app.schemas.support import SupportTaskType
from app.services.job_assistant_service import build_job_task_result
from app.services.research_assistant_service import build_research_task_result
from app.services.support_copilot_service import build_support_task_result

WORKSPACE_RESEARCH_AGENT_NAME = "workspace_research_agent"
WORKSPACE_SUPPORT_AGENT_NAME = "workspace_support_agent"
WORKSPACE_JOB_AGENT_NAME = "workspace_job_agent"


class WorkspaceResearchState(TypedDict, total=False):
    agent_run_id: str
    workspace_id: str
    user_id: str
    task_type: ResearchTaskType
    goal: str
    research_input: dict[str, object]
    research_lineage: dict[str, object]
    should_search: bool
    documents: list[dict[str, object]]
    document_count: int
    matches: list[dict[str, object]]
    tool_call_ids: list[str]
    final_output: dict[str, object]


class WorkspaceSupportState(TypedDict, total=False):
    agent_run_id: str
    workspace_id: str
    user_id: str
    task_type: SupportTaskType
    goal: str
    support_input: dict[str, object]
    support_lineage: dict[str, object]
    should_search: bool
    documents: list[dict[str, object]]
    document_count: int
    matches: list[dict[str, object]]
    tool_call_ids: list[str]
    final_output: dict[str, object]


class WorkspaceJobState(TypedDict, total=False):
    agent_run_id: str
    workspace_id: str
    user_id: str
    task_type: JobTaskType
    goal: str
    job_input: dict[str, object]
    job_comparison_candidates: list[dict[str, object]]
    should_search: bool
    documents: list[dict[str, object]]
    document_count: int
    matches: list[dict[str, object]]
    tool_call_ids: list[str]
    final_output: dict[str, object]


def _plan_goal(state: dict[str, object]) -> dict[str, object]:
    goal = state.get("goal", "")
    resolved_goal = goal.strip() if isinstance(goal, str) else ""
    return {
        "goal": resolved_goal,
        "should_search": bool(resolved_goal),
    }


def _list_workspace_documents(state: dict[str, object]) -> dict[str, object]:
    result = invoke_tool(
        agent_run_id=cast(str, state["agent_run_id"]),
        workspace_id=cast(str, state["workspace_id"]),
        user_id=cast(str, state["user_id"]),
        tool_name="list_workspace_documents",
        tool_input={"limit": 20},
    )
    documents = cast(list[dict[str, object]], result.output["documents"])
    tool_call_ids = [*cast(list[str], state.get("tool_call_ids", [])), result.tool_call_id]
    return {
        "documents": documents,
        "document_count": len(documents),
        "tool_call_ids": tool_call_ids,
    }


def _should_search(state: dict[str, object]) -> str:
    if not state.get("should_search"):
        return "compose_result"
    if not state.get("documents"):
        return "compose_result"
    return "search_documents"


def _search_documents(state: dict[str, object]) -> dict[str, object]:
    result = invoke_tool(
        agent_run_id=cast(str, state["agent_run_id"]),
        workspace_id=cast(str, state["workspace_id"]),
        user_id=cast(str, state["user_id"]),
        tool_name="search_documents",
        tool_input={"query": cast(str, state["goal"]), "limit": 4},
    )
    tool_call_ids = [*cast(list[str], state.get("tool_call_ids", [])), result.tool_call_id]
    return {
        "matches": cast(list[dict[str, object]], result.output["matches"]),
        "tool_call_ids": tool_call_ids,
    }


def _compose_research_result(state: WorkspaceResearchState) -> WorkspaceResearchState:
    documents = state.get("documents", [])
    matches = state.get("matches", [])

    return {
        "final_output": build_research_task_result(
            task_type=state["task_type"],
            research_input=state.get("research_input"),
            lineage=state.get("research_lineage"),
            documents=documents,
            matches=matches,
            tool_call_ids=state.get("tool_call_ids", []),
        ),
    }


def _compose_support_result(state: WorkspaceSupportState) -> WorkspaceSupportState:
    documents = state.get("documents", [])
    matches = state.get("matches", [])

    return {
        "final_output": build_support_task_result(
            task_type=state["task_type"],
            support_input=state.get("support_input"),
            lineage=state.get("support_lineage"),
            documents=documents,
            matches=matches,
            tool_call_ids=state.get("tool_call_ids", []),
        ),
    }


def _compose_job_result(state: WorkspaceJobState) -> WorkspaceJobState:
    documents = state.get("documents", [])
    matches = state.get("matches", [])

    return {
        "final_output": build_job_task_result(
            task_type=state["task_type"],
            job_input=state.get("job_input"),
            comparison_candidates=state.get("job_comparison_candidates"),
            documents=documents,
            matches=matches,
            tool_call_ids=state.get("tool_call_ids", []),
        ),
    }


def _build_workspace_graph(
    *,
    state_schema: Any,
    plan_step_name: str,
    compose_result: Any,
) -> Any:
    # Research, Support, and Job share the same graph skeleton; only the
    # final composition step and plan-step label differ by module.
    workflow = StateGraph(state_schema)
    workflow.add_node(plan_step_name, cast(Any, _plan_goal))
    workflow.add_node("list_workspace_documents", cast(Any, _list_workspace_documents))
    workflow.add_node("search_documents", cast(Any, _search_documents))
    workflow.add_node("compose_result", cast(Any, compose_result))

    workflow.add_edge(START, plan_step_name)
    workflow.add_edge(plan_step_name, "list_workspace_documents")
    workflow.add_conditional_edges(
        "list_workspace_documents",
        _should_search,
        {
            "search_documents": "search_documents",
            "compose_result": "compose_result",
        },
    )
    workflow.add_edge("search_documents", "compose_result")
    workflow.add_edge("compose_result", END)
    return workflow.compile()


def build_workspace_research_graph() -> Any:
    return _build_workspace_graph(
        state_schema=WorkspaceResearchState,
        plan_step_name="plan_research",
        compose_result=_compose_research_result,
    )


def build_workspace_support_graph() -> Any:
    return _build_workspace_graph(
        state_schema=WorkspaceSupportState,
        plan_step_name="plan_support",
        compose_result=_compose_support_result,
    )


def build_workspace_job_graph() -> Any:
    return _build_workspace_graph(
        state_schema=WorkspaceJobState,
        plan_step_name="plan_job",
        compose_result=_compose_job_result,
    )


def _build_workspace_preview(
    *,
    agent_name: str,
    goal: str,
    plan_step_name: str,
) -> dict[str, object]:
    return {
        "agent_name": agent_name,
        "goal": goal,
        "steps": [
            plan_step_name,
            "list_workspace_documents",
            "search_documents",
            "compose_result",
        ],
        "status": "preview",
    }


def build_workspace_research_preview(goal: str) -> dict[str, object]:
    return _build_workspace_preview(
        agent_name=WORKSPACE_RESEARCH_AGENT_NAME,
        goal=goal,
        plan_step_name="plan_research",
    )


def build_workspace_support_preview(goal: str) -> dict[str, object]:
    return _build_workspace_preview(
        agent_name=WORKSPACE_SUPPORT_AGENT_NAME,
        goal=goal,
        plan_step_name="plan_support",
    )


def build_workspace_job_preview(goal: str) -> dict[str, object]:
    return _build_workspace_preview(
        agent_name=WORKSPACE_JOB_AGENT_NAME,
        goal=goal,
        plan_step_name="plan_job",
    )
