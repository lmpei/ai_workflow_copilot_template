from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now


class EvalCase(Base):
    __tablename__ = "eval_cases"
    __table_args__ = (
        UniqueConstraint("dataset_id", "case_index", name="uq_eval_case_dataset_index"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("eval_datasets.id"), index=True)
    case_index: Mapped[int] = mapped_column(Integer)
    input_json: Mapped[dict] = mapped_column(JSON, default=dict)
    expected_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
