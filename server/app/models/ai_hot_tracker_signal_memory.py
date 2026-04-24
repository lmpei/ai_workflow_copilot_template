from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now


class AiHotTrackerSignalMemory(Base):
    __tablename__ = "ai_hot_tracker_signal_memory"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "fingerprint",
            name="uq_ai_hot_tracker_signal_memory_workspace_fingerprint",
        ),
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    fingerprint: Mapped[str] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(50), index=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    continuity_state: Mapped[str] = mapped_column(String(20), default="continuing")
    activity_state: Mapped[str] = mapped_column(String(20), default="continuing")
    source_families_json: Mapped[list] = mapped_column(JSON, default=list)
    source_item_ids_json: Mapped[list] = mapped_column(JSON, default=list)
    source_labels_json: Mapped[list] = mapped_column(JSON, default=list)
    latest_priority_level: Mapped[str] = mapped_column(String(10), default="low")
    latest_rank_score: Mapped[float] = mapped_column(Float(), default=0.0)
    last_seen_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("ai_hot_tracker_tracking_runs.id"),
        nullable=True,
    )
    streak_count: Mapped[int] = mapped_column(default=0)
    cooling_since: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    superseded_by_event_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    last_cluster_snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    note: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
