from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now


class JobHiringPacket(Base):
    __tablename__ = "job_hiring_packets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    created_by: Mapped[str] = mapped_column(String(36), index=True)
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), index=True)
    target_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_role_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    seniority: Mapped[str | None] = mapped_column(String(100), nullable=True)
    latest_task_id: Mapped[str | None] = mapped_column(ForeignKey("tasks.id"), nullable=True, index=True)
    latest_task_type: Mapped[str] = mapped_column(String(100))
    latest_input_json: Mapped[dict] = mapped_column(JSON, default=dict)
    latest_result_json: Mapped[dict] = mapped_column(JSON, default=dict)
    latest_summary: Mapped[str] = mapped_column(Text())
    latest_recommended_outcome: Mapped[str | None] = mapped_column(String(100), nullable=True)
    latest_evidence_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    latest_fit_signal: Mapped[str | None] = mapped_column(String(50), nullable=True)
    latest_shortlist_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    latest_next_steps_json: Mapped[list] = mapped_column(JSON, default=list)
    candidate_labels_json: Mapped[list] = mapped_column(JSON, default=list)
    comparison_history_count: Mapped[int] = mapped_column(Integer(), default=0)
    event_count: Mapped[int] = mapped_column(Integer(), default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
