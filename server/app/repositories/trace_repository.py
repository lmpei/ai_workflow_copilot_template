from datetime import UTC, datetime
from uuid import uuid4

from app.core.database import session_scope
from app.models.trace import Trace


def create_trace(
    *,
    workspace_id: str,
    trace_type: str,
    request_json: dict,
    response_json: dict,
    latency_ms: int,
    token_input: int = 0,
    token_output: int = 0,
    estimated_cost: float = 0.0,
) -> Trace:
    trace = Trace(
        id=str(uuid4()),
        workspace_id=workspace_id,
        trace_type=trace_type,
        request_json=request_json,
        response_json=response_json,
        latency_ms=latency_ms,
        token_input=token_input,
        token_output=token_output,
        estimated_cost=estimated_cost,
        created_at=datetime.now(UTC),
    )
    with session_scope() as session:
        session.add(trace)
        session.flush()
        session.refresh(trace)
        return trace
