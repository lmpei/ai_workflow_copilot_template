from fastapi.testclient import TestClient

from app.schemas.connector import ConnectorConsentGrantRequest, ConnectorConsentRevokeRequest
from app.services import connector_service


def _register_and_login(client: TestClient, *, email: str, name: str) -> dict[str, str]:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "super-secret",
            "name": name,
        },
    )
    assert register_response.status_code == 201
    user = register_response.json()

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "super-secret",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"user_id": user["id"], "token": token}


def _create_workspace(client: TestClient, token: str, *, module_type: str = "research", name: str = "Research Demo") -> str:
    response = client.post(
        "/api/v1/workspaces",
        json={"name": name, "module_type": module_type},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_list_workspace_connectors_returns_research_pilot_status(client: TestClient) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    response = client.get(
        f"/api/v1/workspaces/{workspace_id}/connectors",
        headers=headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["connector"]["id"] == connector_service.RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID
    assert payload[0]["connector"]["kind"] == "external_context"
    assert payload[0]["consent_state"] == "not_granted"


def test_grant_workspace_connector_consent_persists_granted_state(client: TestClient) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/connectors/{connector_service.RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID}/consent",
        json={"consent_note": "允许这个工作区使用一次有边界的外部信息试点。"},
        headers=headers,
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["consent_state"] == "granted"
    assert payload["granted_by"] == auth["user_id"]
    assert payload["consent_note"] == "允许这个工作区使用一次有边界的外部信息试点。"

    get_response = client.get(
        f"/api/v1/workspaces/{workspace_id}/connectors/{connector_service.RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID}",
        headers=headers,
    )
    assert get_response.status_code == 200
    assert get_response.json()["consent_state"] == "granted"


def test_connectors_reject_non_research_workspace(client: TestClient) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"], module_type="support", name="Support Demo")

    response = client.get(
        f"/api/v1/workspaces/{workspace_id}/connectors",
        headers=headers,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "连接器试点目前只对 Research 工作区开放"


def test_require_workspace_connector_consent_enforces_explicit_grant(client: TestClient) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    workspace_id = _create_workspace(client, auth["token"])

    try:
        connector_service.require_workspace_connector_consent(
            workspace_id=workspace_id,
            user_id=auth["user_id"],
            connector_id=connector_service.RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
        )
    except connector_service.ConnectorConsentRequiredError as error:
        assert str(error) == "使用这个外部信息试点前，必须先完成工作区授权"
    else:
        raise AssertionError("Expected connector consent to be required")

    connector_service.grant_workspace_connector_consent(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        connector_id=connector_service.RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
        payload=ConnectorConsentGrantRequest(consent_note="Approved"),
    )
    status = connector_service.require_workspace_connector_consent(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        connector_id=connector_service.RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
    )
    assert status.consent_state == "granted"


def test_revoke_workspace_connector_consent_marks_connector_revoked(client: TestClient) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    grant_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/connectors/{connector_service.RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID}/consent",
        json={"consent_note": "Initial approval"},
        headers=headers,
    )
    assert grant_response.status_code == 201

    revoke_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/connectors/{connector_service.RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID}/consent/revoke",
        json={"consent_note": "Stop using external context for now"},
        headers=headers,
    )
    assert revoke_response.status_code == 200
    payload = revoke_response.json()
    assert payload["consent_state"] == "revoked"
    assert payload["consent_note"] == "Stop using external context for now"
    assert payload["revoked_at"] is not None

    get_response = client.get(
        f"/api/v1/workspaces/{workspace_id}/connectors/{connector_service.RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID}",
        headers=headers,
    )
    assert get_response.status_code == 200
    assert get_response.json()["consent_state"] == "revoked"


def test_require_workspace_connector_consent_rejects_revoked_consent(client: TestClient) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    workspace_id = _create_workspace(client, auth["token"])

    connector_service.grant_workspace_connector_consent(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        connector_id=connector_service.RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
        payload=ConnectorConsentGrantRequest(consent_note="Approved"),
    )
    connector_service.revoke_workspace_connector_consent(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        connector_id=connector_service.RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
        payload=ConnectorConsentRevokeRequest(consent_note="Withdrawn"),
    )

    try:
        connector_service.require_workspace_connector_consent(
            workspace_id=workspace_id,
            user_id=auth["user_id"],
            connector_id=connector_service.RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
        )
    except connector_service.ConnectorConsentRequiredError as error:
        assert error.consent_state == "revoked"
    else:
        raise AssertionError("Expected revoked connector consent to block access")
