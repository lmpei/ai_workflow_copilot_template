from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now


class ResearchExternalResourceSnapshot(Base):
    __tablename__ = "research_external_resource_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    conversation_id: Mapped[str | None] = mapped_column(ForeignKey("conversations.id"), index=True, nullable=True)
    created_by: Mapped[str] = mapped_column(String(36), index=True)
    connector_id: Mapped[str] = mapped_column(String(100), index=True)
    source_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("research_analysis_runs.id"),
        index=True,
        nullable=True,
    )
    title: Mapped[str] = mapped_column(Text())
    analysis_focus: Mapped[str | None] = mapped_column(Text(), nullable=True)
    search_query: Mapped[str] = mapped_column(Text())
    resource_count: Mapped[int] = mapped_column(Integer())
    resources_json: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
