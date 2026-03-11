from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now

DOCUMENT_STATUS_UPLOADED = "uploaded"
DOCUMENT_STATUS_PARSING = "parsing"
DOCUMENT_STATUS_CHUNKED = "chunked"
DOCUMENT_STATUS_INDEXING = "indexing"
DOCUMENT_STATUS_INDEXED = "indexed"
DOCUMENT_STATUS_FAILED = "failed"

DOCUMENT_STATUSES = (
    DOCUMENT_STATUS_UPLOADED,
    DOCUMENT_STATUS_PARSING,
    DOCUMENT_STATUS_CHUNKED,
    DOCUMENT_STATUS_INDEXING,
    DOCUMENT_STATUS_INDEXED,
    DOCUMENT_STATUS_FAILED,
)

DOCUMENT_STATUS_TRANSITIONS = {
    DOCUMENT_STATUS_UPLOADED: {
        DOCUMENT_STATUS_PARSING,
        DOCUMENT_STATUS_FAILED,
    },
    DOCUMENT_STATUS_PARSING: {
        DOCUMENT_STATUS_CHUNKED,
        DOCUMENT_STATUS_FAILED,
    },
    DOCUMENT_STATUS_CHUNKED: {
        DOCUMENT_STATUS_INDEXING,
        DOCUMENT_STATUS_FAILED,
    },
    DOCUMENT_STATUS_INDEXING: {
        DOCUMENT_STATUS_INDEXED,
        DOCUMENT_STATUS_FAILED,
    },
    DOCUMENT_STATUS_INDEXED: {
        DOCUMENT_STATUS_INDEXING,
        DOCUMENT_STATUS_FAILED,
    },
    DOCUMENT_STATUS_FAILED: {
        DOCUMENT_STATUS_PARSING,
        DOCUMENT_STATUS_INDEXING,
    },
}


def is_valid_document_status(status: str) -> bool:
    return status in DOCUMENT_STATUSES


def can_transition_document_status(current_status: str, next_status: str) -> bool:
    if current_status == next_status:
        return True

    if not is_valid_document_status(current_status) or not is_valid_document_status(next_status):
        return False

    return next_status in DOCUMENT_STATUS_TRANSITIONS.get(current_status, set())


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    source_type: Mapped[str] = mapped_column(String(50), default="upload")
    file_path: Mapped[str | None] = mapped_column(Text(), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=DOCUMENT_STATUS_UPLOADED)
    created_by: Mapped[str] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
