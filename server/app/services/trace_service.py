from app.repositories import (
    eval_repository,
    task_repository,
    trace_repository,
    workspace_repository,
)
from app.schemas.analytics import TraceResponse, WorkspaceAnalyticsResponse


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


def get_metrics_snapshot(*, workspace_id: str, user_id: str) -> dict:
    traces = trace_repository.list_traces_for_workspace(workspace_id)
    total_requests = len(traces)
    total_latency_ms = sum(trace.latency_ms for trace in traces)
    token_usage = sum(trace.token_input + trace.token_output for trace in traces)
    total_estimated_cost = round(sum(trace.estimated_cost for trace in traces), 6)
    retrieval_hit_count = sum(
        1
        for trace in traces
        if isinstance(trace.response_json.get("sources"), list)
        and len(trace.response_json["sources"]) > 0
    )
    avg_latency_ms = int(total_latency_ms / total_requests) if total_requests > 0 else 0
    retrieval_hit_rate = (
        round(retrieval_hit_count / total_requests, 4) if total_requests > 0 else 0.0
    )

    tasks = task_repository.list_workspace_tasks(workspace_id, user_id)
    successful_tasks = sum(1 for task in tasks if task.status == "done")
    task_success_rate = round(successful_tasks / len(tasks), 4) if tasks else 0.0

    eval_runs = eval_repository.list_workspace_eval_runs(workspace_id, user_id)
    eval_results = [
        result
        for eval_run in eval_runs
        for result in eval_repository.list_eval_run_results(eval_run.id)
    ]
    scored_values = [float(result.score) for result in eval_results if result.score is not None]
    passed_results = [result for result in eval_results if result.passed is True]
    eval_pass_rate = round(len(passed_results) / len(eval_results), 4) if eval_results else 0.0
    avg_eval_score = (
        round(sum(scored_values) / len(scored_values), 4)
        if scored_values
        else 0.0
    )

    return {
        "workspace_id": workspace_id,
        "total_requests": total_requests,
        "avg_latency_ms": avg_latency_ms,
        "retrieval_hit_count": retrieval_hit_count,
        "retrieval_hit_rate": retrieval_hit_rate,
        "token_usage": token_usage,
        "total_estimated_cost": total_estimated_cost,
        "task_success_rate": task_success_rate,
        "eval_run_count": len(eval_runs),
        "eval_case_count": len(eval_results),
        "eval_pass_rate": eval_pass_rate,
        "avg_eval_score": avg_eval_score,
    }


def get_workspace_metrics(*, workspace_id: str, user_id: str) -> dict:
    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        raise TraceAccessError("Workspace not found")
    return get_metrics_snapshot(workspace_id=workspace_id, user_id=user_id)


def get_workspace_analytics(*, workspace_id: str, user_id: str) -> WorkspaceAnalyticsResponse:
    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        raise TraceAccessError("Workspace not found")
    return WorkspaceAnalyticsResponse(
        **get_metrics_snapshot(workspace_id=workspace_id, user_id=user_id)
    )


def list_workspace_traces(
    *,
    workspace_id: str,
    user_id: str,
    limit: int = 50,
) -> list[TraceResponse]:
    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        raise TraceAccessError("Workspace not found")

    normalized_limit = max(1, min(limit, 200))
    traces = trace_repository.list_traces_for_workspace(workspace_id)
    return [TraceResponse.from_model(trace) for trace in traces[-normalized_limit:]]
