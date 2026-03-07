from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
class Task:
    id: str
    workspace_id: str
    task_type: str
    status: str = "pending"
    created_by: str = "demo-user"
    input_json: dict = field(default_factory=dict)
    output_json: dict = field(default_factory=dict)
    error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
