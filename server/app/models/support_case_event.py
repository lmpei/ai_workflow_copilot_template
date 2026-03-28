from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now


class SupportCaseEvent(Base):
    __tablename__ = "support_case_events"
    __table_args__ = (
        UniqueConstraint("task_id", name="uq_support_case_event_task_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    support_case_id: Mapped[str] = mapped_column(ForeignKey("support_cases.id"), index=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), index=True)
    task_type: Mapped[str] = mapped_column(String(100))
    event_kind: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(Text())
    case_status: Mapped[str] = mapped_column(String(50))
    recommended_owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    evidence_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    should_escalate: Mapped[bool] = mapped_column(Boolean(), default=False)
    needs_manual_review: Mapped[bool] = mapped_column(Boolean(), default=False)
    follow_up_notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
