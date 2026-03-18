from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now


class ResearchAssetRevision(Base):
    __tablename__ = "research_asset_revisions"
    __table_args__ = (
        UniqueConstraint("research_asset_id", "revision_number", name="uq_research_asset_revision_number"),
        UniqueConstraint("task_id", name="uq_research_asset_revision_task_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    research_asset_id: Mapped[str] = mapped_column(ForeignKey("research_assets.id"), index=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), index=True)
    task_type: Mapped[str] = mapped_column(String(100))
    revision_number: Mapped[int] = mapped_column(Integer())
    title: Mapped[str] = mapped_column(String(255))
    input_json: Mapped[dict] = mapped_column(JSON, default=dict)
    result_json: Mapped[dict] = mapped_column(JSON, default=dict)
    summary: Mapped[str] = mapped_column(Text())
    report_headline: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
