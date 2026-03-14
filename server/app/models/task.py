from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now

TASK_STATUS_PENDING = "pending"
TASK_STATUS_RUNNING = "running"
TASK_STATUS_DONE = "done"
TASK_STATUS_FAILED = "failed"

TASK_STATUSES = (
    TASK_STATUS_PENDING,
    TASK_STATUS_RUNNING,
    TASK_STATUS_DONE,
    TASK_STATUS_FAILED,
)

TASK_STATUS_TRANSITIONS = {
    TASK_STATUS_PENDING: {
        TASK_STATUS_RUNNING,
        TASK_STATUS_FAILED,
    },
    TASK_STATUS_RUNNING: {
        TASK_STATUS_DONE,
        TASK_STATUS_FAILED,
    },
    TASK_STATUS_DONE: set(),
    TASK_STATUS_FAILED: set(),
}


def is_valid_task_status(status: str) -> bool:
    return status in TASK_STATUSES


def can_transition_task_status(current_status: str, next_status: str) -> bool:
    if current_status == next_status:
        return True

    if not is_valid_task_status(current_status) or not is_valid_task_status(next_status):
        return False

    return next_status in TASK_STATUS_TRANSITIONS.get(current_status, set())


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    task_type: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default=TASK_STATUS_PENDING, index=True)
    created_by: Mapped[str] = mapped_column(String(36), index=True)
    input_json: Mapped[dict] = mapped_column(JSON, default=dict)
    output_json: Mapped[dict] = mapped_column(JSON, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
