from app.models.workspace_connector_consent import WORKSPACE_CONNECTOR_CONSENT_STATUS_GRANTED
from app.repositories import workspace_connector_consent_repository, workspace_repository
from app.schemas.connector import (
    ConnectorDefinition,
    ConnectorConsentGrantRequest,
    WorkspaceConnectorStatusResponse,
)

RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID = "research_external_context"

_CONNECTOR_DEFINITIONS: dict[str, ConnectorDefinition] = {
    RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID: ConnectorDefinition(
        id=RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
        display_name="Research External Context",
        summary="Allows one bounded Research pilot to use approved external context beyond workspace documents.",
        kind="external_context",
        consent_scope="workspace",
        module_types=["research"],
        requires_consent=True,
    )
}


class ConnectorAccessError(Exception):
    pass


class ConnectorValidationError(Exception):
    pass


class ConnectorConsentRequiredError(Exception):
    pass


def list_connector_definitions(*, module_type: str | None = None) -> list[ConnectorDefinition]:
    definitions = list(_CONNECTOR_DEFINITIONS.values())
    if module_type is None:
        return definitions
    return [definition for definition in definitions if module_type in definition.module_types]


def get_connector_definition(connector_id: str) -> ConnectorDefinition | None:
    return _CONNECTOR_DEFINITIONS.get(connector_id)


def _get_workspace_or_raise(*, workspace_id: str, user_id: str):
    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        raise ConnectorAccessError("Workspace not found")
    if workspace.module_type != "research":
        raise ConnectorValidationError("Connector pilot is only available in Research workspaces")
    return workspace


def _get_connector_definition_or_raise(connector_id: str) -> ConnectorDefinition:
    connector = get_connector_definition(connector_id)
    if connector is None:
        raise ConnectorValidationError(f"Unsupported connector: {connector_id}")
    return connector


def _ensure_connector_available_for_workspace(*, workspace, connector: ConnectorDefinition) -> None:
    if workspace.module_type not in connector.module_types:
        raise ConnectorValidationError("Connector is not available in this workspace")


def _build_workspace_connector_status(
    *,
    connector: ConnectorDefinition,
    workspace_id: str,
    consent,
) -> WorkspaceConnectorStatusResponse:
    consent_granted = consent is not None and consent.status == WORKSPACE_CONNECTOR_CONSENT_STATUS_GRANTED
    return WorkspaceConnectorStatusResponse(
        connector=connector,
        workspace_id=workspace_id,
        consent_state="granted" if consent_granted else "not_granted",
        granted_by=consent.granted_by if consent_granted else None,
        consent_note=consent.consent_note if consent_granted else None,
        granted_at=consent.granted_at if consent_granted else None,
        updated_at=consent.updated_at if consent_granted else None,
    )


def list_workspace_connector_statuses(
    *,
    workspace_id: str,
    user_id: str,
) -> list[WorkspaceConnectorStatusResponse]:
    workspace = _get_workspace_or_raise(workspace_id=workspace_id, user_id=user_id)
    consents = {
        consent.connector_id: consent
        for consent in workspace_connector_consent_repository.list_workspace_connector_consents(workspace_id=workspace.id)
    }
    statuses: list[WorkspaceConnectorStatusResponse] = []
    for connector in list_connector_definitions(module_type=workspace.module_type):
        statuses.append(
            _build_workspace_connector_status(
                connector=connector,
                workspace_id=workspace.id,
                consent=consents.get(connector.id),
            )
        )
    return statuses


def get_workspace_connector_status(
    *,
    workspace_id: str,
    user_id: str,
    connector_id: str,
) -> WorkspaceConnectorStatusResponse:
    workspace = _get_workspace_or_raise(workspace_id=workspace_id, user_id=user_id)
    connector = _get_connector_definition_or_raise(connector_id)
    _ensure_connector_available_for_workspace(workspace=workspace, connector=connector)
    consent = workspace_connector_consent_repository.get_workspace_connector_consent(
        workspace_id=workspace.id,
        connector_id=connector.id,
    )
    return _build_workspace_connector_status(
        connector=connector,
        workspace_id=workspace.id,
        consent=consent,
    )


def grant_workspace_connector_consent(
    *,
    workspace_id: str,
    user_id: str,
    connector_id: str,
    payload: ConnectorConsentGrantRequest,
) -> WorkspaceConnectorStatusResponse:
    workspace = _get_workspace_or_raise(workspace_id=workspace_id, user_id=user_id)
    connector = _get_connector_definition_or_raise(connector_id)
    _ensure_connector_available_for_workspace(workspace=workspace, connector=connector)
    consent = workspace_connector_consent_repository.grant_workspace_connector_consent(
        workspace_id=workspace.id,
        connector_id=connector.id,
        granted_by=user_id,
        consent_note=payload.consent_note.strip() if isinstance(payload.consent_note, str) and payload.consent_note.strip() else None,
    )
    return _build_workspace_connector_status(
        connector=connector,
        workspace_id=workspace.id,
        consent=consent,
    )


def require_workspace_connector_consent(
    *,
    workspace_id: str,
    user_id: str,
    connector_id: str,
) -> WorkspaceConnectorStatusResponse:
    status = get_workspace_connector_status(
        workspace_id=workspace_id,
        user_id=user_id,
        connector_id=connector_id,
    )
    if status.consent_state != "granted":
        raise ConnectorConsentRequiredError("Connector consent is required before using this external context pilot")
    return status
