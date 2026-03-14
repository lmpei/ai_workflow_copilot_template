from app.repositories import trace_repository, workspace_repository


class TraceAccessError(Exception):
    pass


def record_trace(
    *,
    workspace_id: str,
    trace_type: str,
    request_json: dict[str, object],
    response_json: dict[str, object],
    metadata_json: dict[str, object] | None = None,
    parent_trace_id: str | None = None,
    task_id: str | None = None,
    agent_run_id: str | None = None,
    tool_call_id: str | None = None,
    eval_run_id: str | None = None,
    latency_ms: int,
    token_input: int = 0,
    token_output: int = 0,
    estimated_cost: float = 0.0,
    error_message: str | None = None,
) -> str:
    trace = trace_repository.create_trace(
        workspace_id=workspace_id,
        parent_trace_id=parent_trace_id,
        task_id=task_id,
        agent_run_id=agent_run_id,
        tool_call_id=tool_call_id,
        eval_run_id=eval_run_id,
        trace_type=trace_type,
        request_json=request_json,
        response_json=response_json,
        metadata_json=metadata_json,
        error_message=error_message,
        latency_ms=latency_ms,
        token_input=token_input,
        token_output=token_output,
        estimated_cost=estimated_cost,
    )
    return trace.id


def record_chat_trace(
    *,
    workspace_id: str,
    conversation_id: str,
    question: str,
    answer: str,
    mode: str,
    sources: list[dict[str, object]],
    retrieved_chunks: list[dict[str, object]],
    prompt: str,
    latency_ms: int,
    token_input: int = 0,
    token_output: int = 0,
    estimated_cost: float = 0.0,
    error: str | None = None,
    parent_trace_id: str | None = None,
    task_id: str | None = None,
    agent_run_id: str | None = None,
    tool_call_id: str | None = None,
    eval_run_id: str | None = None,
) -> str:
    return record_trace(
        workspace_id=workspace_id,
        parent_trace_id=parent_trace_id,
        task_id=task_id,
        agent_run_id=agent_run_id,
        tool_call_id=tool_call_id,
        eval_run_id=eval_run_id,
        trace_type="rag",
        request_json={
            "conversation_id": conversation_id,
            "question": question,
            "mode": mode,
            "prompt": prompt,
            "retrieved_chunks": retrieved_chunks,
        },
        response_json={
            "answer": answer,
            "sources": sources,
            "error": error,
        },
        metadata_json={
            "prompt": prompt,
            "retrieved_chunks": retrieved_chunks,
        },
        error_message=error,
        latency_ms=latency_ms,
        token_input=token_input,
        token_output=token_output,
        estimated_cost=estimated_cost,
    )


def get_metrics_snapshot(workspace_id: str) -> dict:
    traces = trace_repository.list_traces_for_workspace(workspace_id)
    total_requests = len(traces)
    total_latency_ms = sum(trace.latency_ms for trace in traces)
    token_usage = sum(trace.token_input + trace.token_output for trace in traces)
    retrieval_hit_count = sum(
        1
        for trace in traces
        if isinstance(trace.response_json.get("sources"), list)
        and len(trace.response_json["sources"]) > 0
    )
    avg_latency_ms = int(total_latency_ms / total_requests) if total_requests > 0 else 0

    return {
        "workspace_id": workspace_id,
        "total_requests": total_requests,
        "avg_latency_ms": avg_latency_ms,
        "retrieval_hit_count": retrieval_hit_count,
        "token_usage": token_usage,
        "task_success_rate": 0.0,
    }


def get_workspace_metrics(*, workspace_id: str, user_id: str) -> dict:
    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        raise TraceAccessError("Workspace not found")
    return get_metrics_snapshot(workspace_id=workspace_id)
