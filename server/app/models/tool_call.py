from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now

TOOL_CALL_STATUS_PENDING = "pending"
TOOL_CALL_STATUS_RUNNING = "running"
TOOL_CALL_STATUS_COMPLETED = "completed"
TOOL_CALL_STATUS_FAILED = "failed"

TOOL_CALL_STATUSES = (
    TOOL_CALL_STATUS_PENDING,
    TOOL_CALL_STATUS_RUNNING,
    TOOL_CALL_STATUS_COMPLETED,
    TOOL_CALL_STATUS_FAILED,
)

TOOL_CALL_STATUS_TRANSITIONS = {
    TOOL_CALL_STATUS_PENDING: {
        TOOL_CALL_STATUS_RUNNING,
        TOOL_CALL_STATUS_FAILED,
    },
    TOOL_CALL_STATUS_RUNNING: {
        TOOL_CALL_STATUS_COMPLETED,
        TOOL_CALL_STATUS_FAILED,
    },
    TOOL_CALL_STATUS_COMPLETED: set(),
    TOOL_CALL_STATUS_FAILED: set(),
}


def is_valid_tool_call_status(status: str) -> bool:
    return status in TOOL_CALL_STATUSES


def can_transition_tool_call_status(current_status: str, next_status: str) -> bool:
    if current_status == next_status:
        return True

    if not is_valid_tool_call_status(current_status) or not is_valid_tool_call_status(next_status):
        return False

    return next_status in TOOL_CALL_STATUS_TRANSITIONS.get(current_status, set())


class ToolCall(Base):
    __tablename__ = "tool_calls"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    agent_run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id"), index=True)
    tool_name: Mapped[str] = mapped_column(String(100))
    tool_input_json: Mapped[dict] = mapped_column(JSON, default=dict)
    tool_output_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=TOOL_CALL_STATUS_PENDING, index=True)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
