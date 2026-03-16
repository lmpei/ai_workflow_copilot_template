from typing import TypedDict, cast

from langgraph.graph import END, START, StateGraph

from app.agents.tool_registry import invoke_tool
from app.schemas.research import ResearchTaskType
from app.services.research_assistant_service import build_research_task_result

WORKSPACE_RESEARCH_AGENT_NAME = "workspace_research_agent"


class WorkspaceResearchState(TypedDict, total=False):
    agent_run_id: str
    workspace_id: str
    user_id: str
    task_type: ResearchTaskType
    goal: str
    should_search: bool
    documents: list[dict[str, object]]
    document_count: int
    matches: list[dict[str, object]]
    tool_call_ids: list[str]
    final_output: dict[str, object]



def _plan_research(state: WorkspaceResearchState) -> WorkspaceResearchState:
    return {
        "goal": state.get("goal", "").strip(),
        "should_search": bool(state.get("goal", "").strip()),
    }



def _list_workspace_documents(state: WorkspaceResearchState) -> WorkspaceResearchState:
    result = invoke_tool(
        agent_run_id=state["agent_run_id"],
        workspace_id=state["workspace_id"],
        user_id=state["user_id"],
        tool_name="list_workspace_documents",
        tool_input={"limit": 20},
    )
    documents = cast(list[dict[str, object]], result.output["documents"])
    tool_call_ids = [*state.get("tool_call_ids", []), result.tool_call_id]
    return {
        "documents": documents,
        "document_count": len(documents),
        "tool_call_ids": tool_call_ids,
    }



def _should_search(state: WorkspaceResearchState) -> str:
    if not state.get("should_search"):
        return "compose_result"
    if not state.get("documents"):
        return "compose_result"
    return "search_documents"



def _search_documents(state: WorkspaceResearchState) -> WorkspaceResearchState:
    result = invoke_tool(
        agent_run_id=state["agent_run_id"],
        workspace_id=state["workspace_id"],
        user_id=state["user_id"],
        tool_name="search_documents",
        tool_input={"query": state["goal"], "limit": 4},
    )
    tool_call_ids = [*state.get("tool_call_ids", []), result.tool_call_id]
    return {
        "matches": cast(list[dict[str, object]], result.output["matches"]),
        "tool_call_ids": tool_call_ids,
    }



def _compose_result(state: WorkspaceResearchState) -> WorkspaceResearchState:
    documents = state.get("documents", [])
    matches = state.get("matches", [])

    return {
        "final_output": build_research_task_result(
            task_type=state["task_type"],
            goal=state.get("goal", ""),
            documents=documents,
            matches=matches,
            tool_call_ids=state.get("tool_call_ids", []),
        ),
    }



def build_workspace_research_graph():
    workflow = StateGraph(WorkspaceResearchState)
    workflow.add_node("plan_research", _plan_research)
    workflow.add_node("list_workspace_documents", _list_workspace_documents)
    workflow.add_node("search_documents", _search_documents)
    workflow.add_node("compose_result", _compose_result)

    workflow.add_edge(START, "plan_research")
    workflow.add_edge("plan_research", "list_workspace_documents")
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



def build_workspace_research_preview(goal: str) -> dict[str, object]:
    return {
        "agent_name": WORKSPACE_RESEARCH_AGENT_NAME,
        "goal": goal,
        "steps": [
            "plan_research",
            "list_workspace_documents",
            "search_documents",
            "compose_result",
        ],
        "status": "preview",
    }
