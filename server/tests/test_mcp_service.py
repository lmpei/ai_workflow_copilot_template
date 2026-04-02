from fastapi.testclient import TestClient

from app.schemas.connector import ConnectorConsentGrantRequest
from app.services import connector_service, mcp_service


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


def test_read_workspace_mcp_resource_requires_connector_consent(client: TestClient) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    workspace_id = _create_workspace(client, auth["token"])

    try:
        mcp_service.read_workspace_mcp_resource(
            workspace_id=workspace_id,
            user_id=auth["user_id"],
            connector_id=connector_service.RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
            resource_id=mcp_service.RESEARCH_CONTEXT_DIGEST_RESOURCE_ID,
            query="pricing pressure",
        )
    except connector_service.ConnectorConsentRequiredError as error:
        assert error.consent_state == "not_granted"
    else:
        raise AssertionError("Expected MCP resource access to require connector consent")


def test_read_workspace_mcp_resource_returns_local_digest_after_consent(client: TestClient) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    workspace_id = _create_workspace(client, auth["token"])
    connector_service.grant_workspace_connector_consent(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        connector_id=connector_service.RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
        payload=ConnectorConsentGrantRequest(consent_note="Approved"),
    )

    result = mcp_service.read_workspace_mcp_resource(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        connector_id=connector_service.RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
        resource_id=mcp_service.RESEARCH_CONTEXT_DIGEST_RESOURCE_ID,
        query="pricing pressure",
    )

    assert result.server.id == mcp_service.RESEARCH_CONTEXT_LOCAL_MCP_SERVER_ID
    assert result.resource.id == mcp_service.RESEARCH_CONTEXT_DIGEST_RESOURCE_ID
    assert result.resource_count >= 1
    assert "来源：" in result.text
    assert len(result.items) >= 1
