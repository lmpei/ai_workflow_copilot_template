from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now


class JobHiringPacketEvent(Base):
    __tablename__ = "job_hiring_packet_events"
    __table_args__ = (
        UniqueConstraint("task_id", name="uq_job_hiring_packet_event_task_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_hiring_packet_id: Mapped[str] = mapped_column(ForeignKey("job_hiring_packets.id"), index=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), index=True)
    task_type: Mapped[str] = mapped_column(String(100))
    event_kind: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(String(1000))
    packet_status: Mapped[str] = mapped_column(String(50))
    candidate_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fit_signal: Mapped[str | None] = mapped_column(String(50), nullable=True)
    evidence_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    recommended_outcome: Mapped[str | None] = mapped_column(String(100), nullable=True)
    comparison_task_ids_json: Mapped[list] = mapped_column(JSON, default=list)
    shortlist_entry_count: Mapped[int] = mapped_column(Integer(), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
