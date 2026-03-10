from app.repositories import trace_repository


def record_chat_trace(
    *,
    workspace_id: str,
    conversation_id: str,
    question: str,
    answer: str,
    mode: str,
    sources: list[dict[str, str]],
    latency_ms: int,
) -> str:
    trace = trace_repository.create_trace(
        workspace_id=workspace_id,
        trace_type="rag",
        request_json={
            "conversation_id": conversation_id,
            "question": question,
            "mode": mode,
        },
        response_json={
            "answer": answer,
            "sources": sources,
        },
        latency_ms=latency_ms,
        token_input=0,
        token_output=0,
        estimated_cost=0.0,
    )
    return trace.id


def get_metrics_snapshot(workspace_id: str) -> dict:
    return {
        "workspace_id": workspace_id,
        "total_requests": 0,
        "avg_latency_ms": 0,
        "retrieval_hit_count": 0,
        "token_usage": 0,
        "task_success_rate": 0.0,
    }
