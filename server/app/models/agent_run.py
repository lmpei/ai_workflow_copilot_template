from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now

AGENT_RUN_STATUS_PENDING = "pending"
AGENT_RUN_STATUS_RUNNING = "running"
AGENT_RUN_STATUS_COMPLETED = "completed"
AGENT_RUN_STATUS_FAILED = "failed"

AGENT_RUN_STATUSES = (
    AGENT_RUN_STATUS_PENDING,
    AGENT_RUN_STATUS_RUNNING,
    AGENT_RUN_STATUS_COMPLETED,
    AGENT_RUN_STATUS_FAILED,
)

AGENT_RUN_STATUS_TRANSITIONS = {
    AGENT_RUN_STATUS_PENDING: {
        AGENT_RUN_STATUS_RUNNING,
        AGENT_RUN_STATUS_FAILED,
    },
    AGENT_RUN_STATUS_RUNNING: {
        AGENT_RUN_STATUS_COMPLETED,
        AGENT_RUN_STATUS_FAILED,
    },
    AGENT_RUN_STATUS_COMPLETED: set(),
    AGENT_RUN_STATUS_FAILED: set(),
}


def is_valid_agent_run_status(status: str) -> bool:
    return status in AGENT_RUN_STATUSES


def can_transition_agent_run_status(current_status: str, next_status: str) -> bool:
    if current_status == next_status:
        return True

    if not is_valid_agent_run_status(current_status) or not is_valid_agent_run_status(next_status):
        return False

    return next_status in AGENT_RUN_STATUS_TRANSITIONS.get(current_status, set())


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), index=True)
    agent_name: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default=AGENT_RUN_STATUS_PENDING, index=True)
    final_output: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
