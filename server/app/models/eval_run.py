from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now

EVAL_RUN_STATUS_PENDING = "pending"
EVAL_RUN_STATUS_RUNNING = "running"
EVAL_RUN_STATUS_COMPLETED = "completed"
EVAL_RUN_STATUS_FAILED = "failed"

EVAL_RUN_STATUSES = (
    EVAL_RUN_STATUS_PENDING,
    EVAL_RUN_STATUS_RUNNING,
    EVAL_RUN_STATUS_COMPLETED,
    EVAL_RUN_STATUS_FAILED,
)

EVAL_RUN_STATUS_TRANSITIONS = {
    EVAL_RUN_STATUS_PENDING: {
        EVAL_RUN_STATUS_RUNNING,
        EVAL_RUN_STATUS_FAILED,
    },
    EVAL_RUN_STATUS_RUNNING: {
        EVAL_RUN_STATUS_COMPLETED,
        EVAL_RUN_STATUS_FAILED,
    },
    EVAL_RUN_STATUS_COMPLETED: set(),
    EVAL_RUN_STATUS_FAILED: set(),
}



def is_valid_eval_run_status(status: str) -> bool:
    return status in EVAL_RUN_STATUSES



def can_transition_eval_run_status(current_status: str, next_status: str) -> bool:
    if current_status == next_status:
        return True

    if not is_valid_eval_run_status(current_status) or not is_valid_eval_run_status(next_status):
        return False

    return next_status in EVAL_RUN_STATUS_TRANSITIONS.get(current_status, set())


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("eval_datasets.id"), index=True)
    eval_type: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(50), default=EVAL_RUN_STATUS_PENDING, index=True)
    created_by: Mapped[str] = mapped_column(String(36), index=True)
    summary_json: Mapped[dict] = mapped_column(JSON, default=dict)
    control_json: Mapped[dict] = mapped_column(JSON, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
