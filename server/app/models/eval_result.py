from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now

EVAL_RESULT_STATUS_PENDING = "pending"
EVAL_RESULT_STATUS_COMPLETED = "completed"
EVAL_RESULT_STATUS_FAILED = "failed"

EVAL_RESULT_STATUSES = (
    EVAL_RESULT_STATUS_PENDING,
    EVAL_RESULT_STATUS_COMPLETED,
    EVAL_RESULT_STATUS_FAILED,
)

EVAL_RESULT_STATUS_TRANSITIONS = {
    EVAL_RESULT_STATUS_PENDING: {
        EVAL_RESULT_STATUS_COMPLETED,
        EVAL_RESULT_STATUS_FAILED,
    },
    EVAL_RESULT_STATUS_COMPLETED: set(),
    EVAL_RESULT_STATUS_FAILED: set(),
}



def is_valid_eval_result_status(status: str) -> bool:
    return status in EVAL_RESULT_STATUSES



def can_transition_eval_result_status(current_status: str, next_status: str) -> bool:
    if current_status == next_status:
        return True

    if (
        not is_valid_eval_result_status(current_status)
        or not is_valid_eval_result_status(next_status)
    ):
        return False

    return next_status in EVAL_RESULT_STATUS_TRANSITIONS.get(current_status, set())


class EvalResult(Base):
    __tablename__ = "eval_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    eval_run_id: Mapped[str] = mapped_column(ForeignKey("eval_runs.id"), index=True)
    eval_case_id: Mapped[str] = mapped_column(ForeignKey("eval_cases.id"), index=True)
    status: Mapped[str] = mapped_column(String(50), default=EVAL_RESULT_STATUS_PENDING, index=True)
    output_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metrics_json: Mapped[dict] = mapped_column(JSON, default=dict)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
