def get_metrics_snapshot(workspace_id: str) -> dict:
    return {
        "workspace_id": workspace_id,
        "total_requests": 0,
        "avg_latency_ms": 0,
        "retrieval_hit_count": 0,
        "token_usage": 0,
        "task_success_rate": 0.0,
    }
