from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select

from app.core.database import session_scope
from app.models.workspace_connector_consent import (
    WORKSPACE_CONNECTOR_CONSENT_STATUS_GRANTED,
    WorkspaceConnectorConsent,
    is_valid_workspace_connector_consent_status,
)


def get_workspace_connector_consent(
    *,
    workspace_id: str,
    connector_id: str,
) -> WorkspaceConnectorConsent | None:
    with session_scope() as session:
        statement = select(WorkspaceConnectorConsent).where(
            WorkspaceConnectorConsent.workspace_id == workspace_id,
            WorkspaceConnectorConsent.connector_id == connector_id,
        )
        return session.scalar(statement)


def list_workspace_connector_consents(
    *,
    workspace_id: str,
) -> list[WorkspaceConnectorConsent]:
    with session_scope() as session:
        statement = (
            select(WorkspaceConnectorConsent)
            .where(WorkspaceConnectorConsent.workspace_id == workspace_id)
            .order_by(WorkspaceConnectorConsent.created_at.asc(), WorkspaceConnectorConsent.connector_id.asc())
        )
        return list(session.scalars(statement))


def grant_workspace_connector_consent(
    *,
    workspace_id: str,
    connector_id: str,
    granted_by: str,
    consent_note: str | None = None,
) -> WorkspaceConnectorConsent:
    now = datetime.now(UTC)
    with session_scope() as session:
        statement = select(WorkspaceConnectorConsent).where(
            WorkspaceConnectorConsent.workspace_id == workspace_id,
            WorkspaceConnectorConsent.connector_id == connector_id,
        )
        consent = session.scalar(statement)
        if consent is None:
            consent = WorkspaceConnectorConsent(
                id=str(uuid4()),
                workspace_id=workspace_id,
                connector_id=connector_id,
                granted_by=granted_by,
                status=WORKSPACE_CONNECTOR_CONSENT_STATUS_GRANTED,
                consent_note=consent_note,
                granted_at=now,
                revoked_at=None,
                created_at=now,
                updated_at=now,
            )
        else:
            consent.granted_by = granted_by
            consent.status = WORKSPACE_CONNECTOR_CONSENT_STATUS_GRANTED
            consent.consent_note = consent_note
            consent.granted_at = now
            consent.revoked_at = None
            consent.updated_at = now

        session.add(consent)
        session.flush()
        session.refresh(consent)
        return consent


def update_workspace_connector_consent_status(
    consent_id: str,
    *,
    next_status: str,
    revoked_at: datetime | None = None,
    consent_note: str | None = None,
) -> WorkspaceConnectorConsent | None:
    if not is_valid_workspace_connector_consent_status(next_status):
        raise ValueError(f"Unsupported connector consent status: {next_status}")

    with session_scope() as session:
        consent = session.get(WorkspaceConnectorConsent, consent_id)
        if consent is None:
            return None

        consent.status = next_status
        consent.revoked_at = revoked_at
        if consent_note is not None:
            consent.consent_note = consent_note
        consent.updated_at = datetime.now(UTC)
        session.add(consent)
        session.flush()
        session.refresh(consent)
        return consent
