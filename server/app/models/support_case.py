from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now


class SupportCase(Base):
    __tablename__ = "support_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    created_by: Mapped[str] = mapped_column(String(36), index=True)
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), index=True)
    latest_task_id: Mapped[str | None] = mapped_column(ForeignKey("tasks.id"), nullable=True, index=True)
    latest_task_type: Mapped[str] = mapped_column(String(100))
    latest_input_json: Mapped[dict] = mapped_column(JSON, default=dict)
    latest_result_json: Mapped[dict] = mapped_column(JSON, default=dict)
    latest_summary: Mapped[str] = mapped_column(Text())
    latest_recommended_owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    latest_evidence_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    event_count: Mapped[int] = mapped_column(Integer(), default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
