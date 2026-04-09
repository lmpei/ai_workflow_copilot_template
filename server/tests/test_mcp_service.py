import json
import sys

from app.core.config import get_settings
from app.schemas.connector import ConnectorConsentGrantRequest
from app.schemas.mcp import (
    AI_FRONTIER_BRIEF_PROMPT_NAME,
    AI_FRONTIER_DIGEST_RESOURCE_ID,
    AI_FRONTIER_DIGEST_RESOURCE_URI,
    AI_FRONTIER_EXTERNAL_MCP_SERVER_ID,
    AI_FRONTIER_LOCAL_MCP_SERVER_ID,
    AI_FRONTIER_SEARCH_TOOL_NAME,
    AI_FRONTIER_STDIO_MCP_SERVER_ID,
)
from app.services import connector_service, mcp_service


def _register_and_login(client, *, email: str, name: str) -> dict[str, str]:
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


def _create_workspace(client, token: str, *, module_type: str = "research", name: str = "Research Demo") -> str:
    response = client.post(
        "/api/v1/workspaces",
        json={"name": name, "module_type": module_type},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _enable_configured_external_endpoint(
    monkeypatch,
    *,
    auth_required: bool = False,
    auth_token: str = "test-token",
    expected_token: str | None = None,
) -> None:
    monkeypatch.setenv("RESEARCH_EXTERNAL_MCP_ENABLED", "true")
    monkeypatch.setenv(
        "RESEARCH_EXTERNAL_MCP_COMMAND",
        json.dumps([sys.executable, "-m", "app.mcp.research_context_stdio_server"]),
    )
    monkeypatch.setenv("RESEARCH_EXTERNAL_MCP_WORKING_DIRECTORY", str(mcp_service._SERVER_ROOT))
    monkeypatch.setenv("RESEARCH_EXTERNAL_MCP_SERVER_ID", AI_FRONTIER_EXTERNAL_MCP_SERVER_ID)
    monkeypatch.setenv("RESEARCH_EXTERNAL_MCP_SERVER_DISPLAY_NAME", "AI 前沿研究外部 MCP 服务")
    monkeypatch.setenv("RESEARCH_EXTERNAL_MCP_RESOURCE_ID", AI_FRONTIER_DIGEST_RESOURCE_ID)
    monkeypatch.setenv("RESEARCH_EXTERNAL_MCP_RESOURCE_URI", AI_FRONTIER_DIGEST_RESOURCE_URI)
    monkeypatch.setenv("RESEARCH_EXTERNAL_MCP_AUTH_REQUIRED", "true" if auth_required else "false")
    monkeypatch.setenv("RESEARCH_EXTERNAL_MCP_AUTH_TOKEN", auth_token if auth_required else "")
    monkeypatch.setenv(
        "RESEARCH_EXTERNAL_MCP_EXPECTED_AUTH_TOKEN",
        expected_token if expected_token is not None else (auth_token if auth_required else ""),
    )
    get_settings.cache_clear()


def test_read_workspace_mcp_resource_requires_connector_consent(client) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    workspace_id = _create_workspace(client, auth["token"])

    try:
        mcp_service.read_workspace_mcp_resource(
            workspace_id=workspace_id,
            user_id=auth["user_id"],
            connector_id=connector_service.RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
            resource_id=AI_FRONTIER_DIGEST_RESOURCE_ID,
            query="pricing pressure",
        )
    except connector_service.ConnectorConsentRequiredError as error:
        assert error.consent_state == "not_granted"
    else:
        raise AssertionError("Expected MCP resource access to require connector consent")


def test_read_workspace_mcp_resource_returns_local_digest_after_consent(client) -> None:
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
        resource_id=AI_FRONTIER_DIGEST_RESOURCE_ID,
        query="pricing pressure",
    )

    assert result.server.id == AI_FRONTIER_LOCAL_MCP_SERVER_ID
    assert result.resource.id == AI_FRONTIER_DIGEST_RESOURCE_ID
    assert result.resource_count >= 1
    assert len(result.items) >= 1


def test_describe_workspace_remote_mcp_server_returns_repo_local_process_server_metadata(client) -> None:
    auth = _register_and_login(client, email="remote-owner@example.com", name="Remote Owner")
    workspace_id = _create_workspace(client, auth["token"])

    server, resources, tools, prompts = mcp_service.describe_workspace_remote_mcp_server(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        connector_id=connector_service.RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
    )

    assert server.id == AI_FRONTIER_STDIO_MCP_SERVER_ID
    assert server.transport == "stdio_process"
    assert len(resources) == 1
    assert resources[0].id == AI_FRONTIER_DIGEST_RESOURCE_ID
    assert tools == []
    assert prompts == []


def test_validate_workspace_connector_mcp_endpoint_prefers_external_config(monkeypatch, client) -> None:
    _enable_configured_external_endpoint(monkeypatch)
    auth = _register_and_login(client, email="external-validate@example.com", name="External Validate")
    workspace_id = _create_workspace(client, auth["token"])

    result = mcp_service.validate_workspace_connector_mcp_endpoint(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        connector_id=connector_service.RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
    )

    assert result.endpoint.source == "external_configured"
    assert result.endpoint.launch_kind == "command"
    assert result.auth_state == "not_required"
    assert result.health_status == "ready"
    assert result.server is not None
    assert result.server.id == AI_FRONTIER_EXTERNAL_MCP_SERVER_ID
    assert len(result.resources) == 1
    assert result.tools == []
    assert result.prompts == []


def test_validate_workspace_connector_mcp_endpoint_reports_missing_auth(monkeypatch, client) -> None:
    _enable_configured_external_endpoint(monkeypatch, auth_required=True, auth_token="")
    auth = _register_and_login(client, email="external-auth-missing@example.com", name="External Missing")
    workspace_id = _create_workspace(client, auth["token"])

    result = mcp_service.validate_workspace_connector_mcp_endpoint(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        connector_id=connector_service.RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
    )

    assert result.endpoint.source == "external_configured"
    assert result.auth_state == "missing"
    assert result.health_status == "invalid"
    assert result.health_detail


def test_validate_workspace_connector_mcp_endpoint_reports_denied_auth(monkeypatch, client) -> None:
    _enable_configured_external_endpoint(
        monkeypatch,
        auth_required=True,
        auth_token="wrong-token",
        expected_token="expected-token",
    )
    monkeypatch.setattr(
        mcp_service,
        "_describe_remote_server_from_binding",
        lambda **_: (_ for _ in ()).throw(mcp_service.McpRemoteAuthDeniedError("MCP authentication was denied.")),
    )
    auth = _register_and_login(client, email="external-auth-denied@example.com", name="External Denied")
    workspace_id = _create_workspace(client, auth["token"])

    result = mcp_service.validate_workspace_connector_mcp_endpoint(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        connector_id=connector_service.RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
    )

    assert result.endpoint.source == "external_configured"
    assert result.auth_state == "denied"
    assert result.health_status == "invalid"
    assert "denied" in (result.health_detail or "")


def test_read_workspace_remote_mcp_resource_can_use_configured_external_endpoint_after_consent(monkeypatch, client) -> None:
    _enable_configured_external_endpoint(monkeypatch)
    auth = _register_and_login(client, email="remote-read@example.com", name="Remote Read")
    workspace_id = _create_workspace(client, auth["token"])
    connector_service.grant_workspace_connector_consent(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        connector_id=connector_service.RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
        payload=ConnectorConsentGrantRequest(consent_note="Approved"),
    )

    result = mcp_service.read_workspace_remote_mcp_resource(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        connector_id=connector_service.RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
        resource_id=AI_FRONTIER_DIGEST_RESOURCE_ID,
        query="pricing pressure",
    )

    assert result.server.id == AI_FRONTIER_EXTERNAL_MCP_SERVER_ID
    assert result.server.transport == "stdio_process"
    assert result.resource.id == AI_FRONTIER_DIGEST_RESOURCE_ID
    assert result.resource_count >= 1
    assert len(result.items) >= 1


def test_read_workspace_true_external_mcp_resource_requires_external_configuration(client) -> None:
    auth = _register_and_login(client, email="true-external-missing@example.com", name="True External Missing")
    workspace_id = _create_workspace(client, auth["token"])
    connector_service.grant_workspace_connector_consent(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        connector_id=connector_service.RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
        payload=ConnectorConsentGrantRequest(consent_note="Approved"),
    )

    try:
        mcp_service.read_workspace_true_external_mcp_resource(
            workspace_id=workspace_id,
            user_id=auth["user_id"],
            connector_id=connector_service.RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
            resource_id=AI_FRONTIER_DIGEST_RESOURCE_ID,
            query="pricing pressure",
        )
    except mcp_service.McpExternalEndpointNotConfiguredError as error:
        assert "True external MCP endpoint is not configured" in str(error)
    else:
        raise AssertionError("Expected true external MCP access to require external endpoint configuration")


def test_read_workspace_true_external_mcp_resource_requires_auth_when_configured(monkeypatch, client) -> None:
    _enable_configured_external_endpoint(monkeypatch, auth_required=True, auth_token="")
    monkeypatch.setattr(
        mcp_service,
        "_read_remote_resource_from_binding",
        lambda **_: (_ for _ in ()).throw(mcp_service.McpRemoteAuthRequiredError("MCP authentication is required.")),
    )
    auth = _register_and_login(client, email="true-external-auth-required@example.com", name="True External Auth")
    workspace_id = _create_workspace(client, auth["token"])
    connector_service.grant_workspace_connector_consent(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        connector_id=connector_service.RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
        payload=ConnectorConsentGrantRequest(consent_note="Approved"),
    )

    try:
        mcp_service.read_workspace_true_external_mcp_resource(
            workspace_id=workspace_id,
            user_id=auth["user_id"],
            connector_id=connector_service.RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
            resource_id=AI_FRONTIER_DIGEST_RESOURCE_ID,
            query="pricing pressure",
        )
    except mcp_service.McpRemoteAuthRequiredError as error:
        assert "required" in str(error)
    else:
        raise AssertionError("Expected true external MCP access to require auth")
