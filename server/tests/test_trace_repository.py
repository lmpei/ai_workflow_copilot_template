from app.repositories import task_repository, trace_repository, workspace_repository
from app.schemas.workspace import WorkspaceCreate
from app.services import trace_service


def _create_workspace(*, owner_id: str = "user-1") -> str:
    workspace = workspace_repository.create_workspace(
        WorkspaceCreate(name="Trace Demo", type="research"),
        owner_id,
    )
    return workspace.id


def test_trace_repository_persists_related_ids_and_supports_link_queries() -> None:
    workspace_id = _create_workspace()
    task = task_repository.create_task(
        workspace_id=workspace_id,
        task_type="research_summary",
        created_by="user-1",
    )
    agent_run = task_repository.create_agent_run(
        task_id=task.id,
        agent_name="workspace_research_agent",
    )
    tool_call = task_repository.create_tool_call(
        agent_run_id=agent_run.id,
        tool_name="search_documents",
    )

    parent_trace = trace_repository.create_trace(
        workspace_id=workspace_id,
        task_id=task.id,
        trace_type="task",
        request_json={"goal": "summarize"},
        response_json={"status": "started"},
        metadata_json={"worker": "arq"},
        latency_ms=12,
    )
    child_trace = trace_repository.create_trace(
        workspace_id=workspace_id,
        parent_trace_id=parent_trace.id,
        task_id=task.id,
        agent_run_id=agent_run.id,
        tool_call_id=tool_call.id,
        eval_run_id="eval-run-1",
        trace_type="tool_call",
        request_json={"query": "apollo"},
        response_json={"result_count": 1},
        metadata_json={"retrieval_backend": "chroma"},
        error_message="temporary warning",
        latency_ms=34,
        token_input=5,
        token_output=2,
    )

    assert [trace.id for trace in trace_repository.list_traces_for_workspace(workspace_id)] == [
        parent_trace.id,
        child_trace.id,
    ]
    assert [trace.id for trace in trace_repository.list_traces_for_task(task.id)] == [
        parent_trace.id,
        child_trace.id,
    ]
    assert [trace.id for trace in trace_repository.list_traces_for_agent_run(agent_run.id)] == [
        child_trace.id,
    ]
    assert [trace.id for trace in trace_repository.list_traces_for_tool_call(tool_call.id)] == [
        child_trace.id,
    ]
    assert [trace.id for trace in trace_repository.list_traces_for_eval_run("eval-run-1")] == [
        child_trace.id,
    ]
    assert [trace.id for trace in trace_repository.list_child_traces(parent_trace.id)] == [
        child_trace.id,
    ]
    assert child_trace.metadata_json == {"retrieval_backend": "chroma"}
    assert child_trace.error_message == "temporary warning"


def test_record_chat_trace_preserves_existing_payloads_and_adds_phase_four_metadata() -> None:
    workspace_id = _create_workspace(owner_id="user-2")

    trace_id = trace_service.record_chat_trace(
        workspace_id=workspace_id,
        conversation_id="conversation-1",
        question="Who owns Project Apollo?",
        answer="Alice owns Project Apollo.",
        mode="rag",
        sources=[{"document_id": "doc-1", "chunk_id": "chunk-1"}],
        retrieved_chunks=[{"document_id": "doc-1", "chunk_id": "chunk-1"}],
        prompt="grounded prompt",
        latency_ms=101,
        token_input=11,
        token_output=7,
        estimated_cost=0.0,
        error="judge warning",
        task_id="task-1",
        agent_run_id="agent-run-1",
    )

    trace = trace_repository.list_traces_for_workspace(workspace_id)[0]
    assert trace.id == trace_id
    assert trace.task_id == "task-1"
    assert trace.agent_run_id == "agent-run-1"
    assert trace.request_json["prompt"] == "grounded prompt"
    assert trace.metadata_json == {
        "prompt": "grounded prompt",
        "retrieved_chunks": [{"document_id": "doc-1", "chunk_id": "chunk-1"}],
    }
    assert trace.response_json["error"] == "judge warning"
    assert trace.error_message == "judge warning"
