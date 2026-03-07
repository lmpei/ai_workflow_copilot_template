from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
class Trace:
    id: str
    workspace_id: str
    trace_type: str
    request_json: dict = field(default_factory=dict)
    response_json: dict = field(default_factory=dict)
    latency_ms: int = 0
    token_input: int = 0
    token_output: int = 0
    estimated_cost: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
