from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now

RESEARCH_ANALYSIS_RUN_STATUS_PENDING = "pending"
RESEARCH_ANALYSIS_RUN_STATUS_RUNNING = "running"
RESEARCH_ANALYSIS_RUN_STATUS_COMPLETED = "completed"
RESEARCH_ANALYSIS_RUN_STATUS_DEGRADED = "degraded"
RESEARCH_ANALYSIS_RUN_STATUS_FAILED = "failed"

RESEARCH_ANALYSIS_RUN_STATUSES = (
    RESEARCH_ANALYSIS_RUN_STATUS_PENDING,
    RESEARCH_ANALYSIS_RUN_STATUS_RUNNING,
    RESEARCH_ANALYSIS_RUN_STATUS_COMPLETED,
    RESEARCH_ANALYSIS_RUN_STATUS_DEGRADED,
    RESEARCH_ANALYSIS_RUN_STATUS_FAILED,
)

RESEARCH_ANALYSIS_RUN_STATUS_TRANSITIONS = {
    RESEARCH_ANALYSIS_RUN_STATUS_PENDING: {
        RESEARCH_ANALYSIS_RUN_STATUS_RUNNING,
        RESEARCH_ANALYSIS_RUN_STATUS_FAILED,
    },
    RESEARCH_ANALYSIS_RUN_STATUS_RUNNING: {
        RESEARCH_ANALYSIS_RUN_STATUS_COMPLETED,
        RESEARCH_ANALYSIS_RUN_STATUS_DEGRADED,
        RESEARCH_ANALYSIS_RUN_STATUS_FAILED,
    },
    RESEARCH_ANALYSIS_RUN_STATUS_COMPLETED: set(),
    RESEARCH_ANALYSIS_RUN_STATUS_DEGRADED: set(),
    RESEARCH_ANALYSIS_RUN_STATUS_FAILED: set(),
}


def is_valid_research_analysis_run_status(status: str) -> bool:
    return status in RESEARCH_ANALYSIS_RUN_STATUSES


def can_transition_research_analysis_run_status(current_status: str, next_status: str) -> bool:
    if current_status == next_status:
        return True

    if not is_valid_research_analysis_run_status(current_status) or not is_valid_research_analysis_run_status(next_status):
        return False

    return next_status in RESEARCH_ANALYSIS_RUN_STATUS_TRANSITIONS.get(current_status, set())


class ResearchAnalysisRun(Base):
    __tablename__ = "research_analysis_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    created_by: Mapped[str] = mapped_column(String(36), index=True)
    status: Mapped[str] = mapped_column(String(50), default=RESEARCH_ANALYSIS_RUN_STATUS_PENDING, index=True)
    question: Mapped[str] = mapped_column(Text())
    mode: Mapped[str] = mapped_column(String(50), default="research_tool_assisted")
    resumed_from_run_id: Mapped[str | None] = mapped_column(ForeignKey("research_analysis_runs.id"), index=True, nullable=True)
    selected_external_resource_snapshot_id: Mapped[str | None] = mapped_column(
        ForeignKey("research_external_resource_snapshots.id"),
        index=True,
        nullable=True,
    )
    external_resource_snapshot_id: Mapped[str | None] = mapped_column(
        ForeignKey("research_external_resource_snapshots.id"),
        index=True,
        nullable=True,
    )
    prompt: Mapped[str | None] = mapped_column(Text(), nullable=True)
    answer: Mapped[str | None] = mapped_column(Text(), nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    sources_json: Mapped[list] = mapped_column(JSON, default=list)
    tool_steps_json: Mapped[list] = mapped_column(JSON, default=list)
    run_memory_json: Mapped[dict] = mapped_column(JSON, default=dict)
    analysis_focus: Mapped[str | None] = mapped_column(Text(), nullable=True)
    search_query: Mapped[str | None] = mapped_column(Text(), nullable=True)
    degraded_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
