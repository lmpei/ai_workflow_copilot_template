from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now

WORKSPACE_CONNECTOR_CONSENT_STATUS_GRANTED = "granted"
WORKSPACE_CONNECTOR_CONSENT_STATUS_REVOKED = "revoked"

WORKSPACE_CONNECTOR_CONSENT_STATUSES = (
    WORKSPACE_CONNECTOR_CONSENT_STATUS_GRANTED,
    WORKSPACE_CONNECTOR_CONSENT_STATUS_REVOKED,
)


def is_valid_workspace_connector_consent_status(status: str) -> bool:
    return status in WORKSPACE_CONNECTOR_CONSENT_STATUSES


class WorkspaceConnectorConsent(Base):
    __tablename__ = "workspace_connector_consents"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "connector_id",
            name="uq_workspace_connector_consents_workspace_connector",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    connector_id: Mapped[str] = mapped_column(String(100), index=True)
    granted_by: Mapped[str] = mapped_column(String(36), index=True)
    status: Mapped[str] = mapped_column(String(50), default=WORKSPACE_CONNECTOR_CONSENT_STATUS_GRANTED, index=True)
    consent_note: Mapped[str | None] = mapped_column(Text(), nullable=True)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
