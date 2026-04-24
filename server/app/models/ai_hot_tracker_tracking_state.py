from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now


class AiHotTrackerTrackingState(Base):
    __tablename__ = "ai_hot_tracker_tracking_state"

    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id"),
        primary_key=True,
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_successful_scan_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_cluster_snapshot_json: Mapped[list] = mapped_column(JSON, default=list)
    last_saved_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("ai_hot_tracker_tracking_runs.id"),
        nullable=True,
    )
    latest_saved_run_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_notified_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("ai_hot_tracker_tracking_runs.id"),
        nullable=True,
    )
    latest_meaningful_update_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consecutive_failure_count: Mapped[int] = mapped_column(default=0)
    last_error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
