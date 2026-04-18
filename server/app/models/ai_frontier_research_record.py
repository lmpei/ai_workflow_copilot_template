from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now


class AiFrontierResearchRecord(Base):
    __tablename__ = "ai_frontier_research_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    conversation_id: Mapped[str | None] = mapped_column(ForeignKey("conversations.id"), index=True, nullable=True)
    source_run_id: Mapped[str | None] = mapped_column(ForeignKey("research_analysis_runs.id"), index=True, nullable=True)
    source_trace_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    created_by: Mapped[str] = mapped_column(String(36), index=True)
    title: Mapped[str] = mapped_column(String(255))
    question: Mapped[str] = mapped_column(Text())
    frontier_summary: Mapped[str] = mapped_column(Text())
    trend_judgment: Mapped[str] = mapped_column(Text())
    themes_json: Mapped[list] = mapped_column(JSON, default=list)
    events_json: Mapped[list] = mapped_column(JSON, default=list)
    project_cards_json: Mapped[list] = mapped_column(JSON, default=list)
    reference_sources_json: Mapped[list] = mapped_column(JSON, default=list)
    source_set_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
