from datetime import datetime

from pydantic import BaseModel

from app.models.trace import Trace


class WorkspaceAnalyticsResponse(BaseModel):
    workspace_id: str
    total_requests: int
    avg_latency_ms: int
    retrieval_hit_count: int
    retrieval_hit_rate: float
    token_usage: int
    total_estimated_cost: float
    task_success_rate: float
    eval_run_count: int
    eval_case_count: int
    eval_pass_rate: float
    avg_eval_score: float


class TraceResponse(BaseModel):
    id: str
    workspace_id: str
    parent_trace_id: str | None = None
    task_id: str | None = None
    agent_run_id: str | None = None
    tool_call_id: str | None = None
    eval_run_id: str | None = None
    trace_type: str
    request_json: dict[str, object]
    response_json: dict[str, object]
    metadata_json: dict[str, object]
    error_message: str | None = None
    latency_ms: int
    token_input: int
    token_output: int
    estimated_cost: float
    created_at: datetime

    @classmethod
    def from_model(cls, trace: Trace) -> "TraceResponse":
        return cls(
            id=trace.id,
            workspace_id=trace.workspace_id,
            parent_trace_id=trace.parent_trace_id,
            task_id=trace.task_id,
            agent_run_id=trace.agent_run_id,
            tool_call_id=trace.tool_call_id,
            eval_run_id=trace.eval_run_id,
            trace_type=trace.trace_type,
            request_json=trace.request_json,
            response_json=trace.response_json,
            metadata_json=trace.metadata_json,
            error_message=trace.error_message,
            latency_ms=trace.latency_ms,
            token_input=trace.token_input,
            token_output=trace.token_output,
            estimated_cost=trace.estimated_cost,
            created_at=trace.created_at,
        )
