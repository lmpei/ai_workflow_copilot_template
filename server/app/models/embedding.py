from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now


class Embedding(Base):
    __tablename__ = "embeddings"
    __table_args__ = (
        UniqueConstraint(
            "document_chunk_id",
            "collection_name",
            "embedding_model",
            name="uq_chunk_collection_model",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_chunk_id: Mapped[str] = mapped_column(ForeignKey("document_chunks.id"), index=True)
    vector_store_id: Mapped[str] = mapped_column(String(255), unique=True)
    collection_name: Mapped[str] = mapped_column(String(255))
    embedding_model: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
