from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now


class Trace(Base):
    __tablename__ = "traces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    parent_trace_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    task_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    agent_run_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    tool_call_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    eval_run_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    trace_type: Mapped[str] = mapped_column(String(50))
    request_json: Mapped[dict] = mapped_column(JSON, default=dict)
    response_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    token_input: Mapped[int] = mapped_column(Integer, default=0)
    token_output: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
