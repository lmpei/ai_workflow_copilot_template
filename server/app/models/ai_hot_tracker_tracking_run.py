from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now


class AiHotTrackerTrackingRun(Base):
    __tablename__ = "ai_hot_tracker_tracking_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    previous_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("ai_hot_tracker_tracking_runs.id"),
        index=True,
        nullable=True,
    )
    created_by: Mapped[str] = mapped_column(String(36), index=True)
    trigger_kind: Mapped[str] = mapped_column(String(20), default="manual")
    status: Mapped[str] = mapped_column(String(20), default="completed")
    title: Mapped[str] = mapped_column(String(255))
    question: Mapped[str] = mapped_column(Text())
    profile_snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    output_json: Mapped[dict] = mapped_column(JSON, default=dict)
    source_catalog_json: Mapped[list] = mapped_column(JSON, default=list)
    source_items_json: Mapped[list] = mapped_column(JSON, default=list)
    source_failures_json: Mapped[list] = mapped_column(JSON, default=list)
    source_set_json: Mapped[dict] = mapped_column(JSON, default=dict)
    delta_json: Mapped[dict] = mapped_column(JSON, default=dict)
    follow_ups_json: Mapped[list] = mapped_column(JSON, default=list)
    degraded_reason: Mapped[str | None] = mapped_column(Text(), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
