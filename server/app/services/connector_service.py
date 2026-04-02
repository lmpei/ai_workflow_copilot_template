from datetime import UTC, datetime

from app.models.workspace_connector_consent import (
    WORKSPACE_CONNECTOR_CONSENT_STATUS_GRANTED,
    WORKSPACE_CONNECTOR_CONSENT_STATUS_REVOKED,
)
from app.repositories import workspace_connector_consent_repository, workspace_repository
from app.schemas.connector import (
    ConnectorConsentGrantRequest,
    ConnectorConsentRevokeRequest,
    ConnectorDefinition,
    WorkspaceConnectorStatusResponse,
)

RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID = "research_external_context"

_CONNECTOR_DEFINITIONS: dict[str, ConnectorDefinition] = {
    RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID: ConnectorDefinition(
        id=RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
        display_name="Research 外部信息",
        summary="允许一个有边界的 Research 试点在工作区资料之外使用已授权的外部信息。",
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
    def __init__(self, message: str, *, consent_state: str) -> None:
        super().__init__(message)
        self.consent_state = consent_state


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
        raise ConnectorAccessError("工作区不存在。")
    if workspace.module_type != "research":
        raise ConnectorValidationError("连接器试点目前只对 Research 工作区开放。")
    return workspace


def _get_connector_definition_or_raise(connector_id: str) -> ConnectorDefinition:
    connector = get_connector_definition(connector_id)
    if connector is None:
        raise ConnectorValidationError(f"不支持的连接器：{connector_id}")
    return connector


def _ensure_connector_available_for_workspace(*, workspace, connector: ConnectorDefinition) -> None:
    if workspace.module_type not in connector.module_types:
        raise ConnectorValidationError("这个工作区不能使用该连接器。")


def _build_workspace_connector_status(
    *,
    connector: ConnectorDefinition,
    workspace_id: str,
    consent,
) -> WorkspaceConnectorStatusResponse:
    consent_state = "not_granted"
    if consent is not None:
        if consent.status == WORKSPACE_CONNECTOR_CONSENT_STATUS_GRANTED:
            consent_state = "granted"
        elif consent.status == WORKSPACE_CONNECTOR_CONSENT_STATUS_REVOKED:
            consent_state = "revoked"

    return WorkspaceConnectorStatusResponse(
        connector=connector,
        workspace_id=workspace_id,
        consent_state=consent_state,
        granted_by=consent.granted_by if consent is not None else None,
        consent_note=consent.consent_note if consent is not None else None,
        granted_at=consent.granted_at if consent is not None else None,
        revoked_at=consent.revoked_at if consent is not None else None,
        updated_at=consent.updated_at if consent is not None else None,
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


def revoke_workspace_connector_consent(
    *,
    workspace_id: str,
    user_id: str,
    connector_id: str,
    payload: ConnectorConsentRevokeRequest,
) -> WorkspaceConnectorStatusResponse:
    workspace = _get_workspace_or_raise(workspace_id=workspace_id, user_id=user_id)
    connector = _get_connector_definition_or_raise(connector_id)
    _ensure_connector_available_for_workspace(workspace=workspace, connector=connector)
    consent = workspace_connector_consent_repository.get_workspace_connector_consent(
        workspace_id=workspace.id,
        connector_id=connector.id,
    )
    if consent is not None:
        consent = workspace_connector_consent_repository.update_workspace_connector_consent_status(
            consent.id,
            next_status=WORKSPACE_CONNECTOR_CONSENT_STATUS_REVOKED,
            revoked_at=datetime.now(UTC),
            consent_note=payload.consent_note.strip() if isinstance(payload.consent_note, str) and payload.consent_note.strip() else consent.consent_note,
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
        if status.consent_state == "revoked":
            raise ConnectorConsentRequiredError(
                "这个工作区已经撤销了外部信息试点授权，继续使用前需要重新授权。",
                consent_state="revoked",
            )
        raise ConnectorConsentRequiredError(
            "使用这个外部信息试点前，必须先完成工作区授权。",
            consent_state="not_granted",
        )
    return status
