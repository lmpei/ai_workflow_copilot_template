from app.core.config import get_settings
from fastapi.testclient import TestClient


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
    return {
        "user_id": user["id"],
        "token": token,
    }


def test_workspace_crud_requires_auth_and_persists_owner(client: TestClient) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}

    unauthorized_response = client.get("/api/v1/workspaces")
    assert unauthorized_response.status_code == 401

    create_response = client.post(
        "/api/v1/workspaces",
        json={"name": "Research Demo", "type": "research", "description": "Initial workspace"},
        headers=headers,
    )
    assert create_response.status_code == 201

    created = create_response.json()
    workspace_id = created["id"]
    assert created["name"] == "Research Demo"
    assert created["module_type"] == "research"
    assert "type" not in created
    assert created["module_config_json"]["result_type"] == "research_report"
    assert created["owner_id"] == auth["user_id"]

    get_response = client.get(f"/api/v1/workspaces/{workspace_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == workspace_id

    patch_response = client.patch(
        f"/api/v1/workspaces/{workspace_id}",
        json={"description": "Updated description"},
        headers=headers,
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["description"] == "Updated description"

    list_response = client.get("/api/v1/workspaces", headers=headers)
    assert list_response.status_code == 200
    assert any(item["id"] == workspace_id for item in list_response.json())


def test_workspace_list_is_scoped_to_membership(client: TestClient) -> None:
    owner_auth = _register_and_login(client, email="owner@example.com", name="Owner")
    other_auth = _register_and_login(client, email="other@example.com", name="Other")

    owner_headers = {"Authorization": f"Bearer {owner_auth['token']}"}
    other_headers = {"Authorization": f"Bearer {other_auth['token']}"}

    first_workspace = client.post(
        "/api/v1/workspaces",
        json={"name": "Research A", "module_type": "research"},
        headers=owner_headers,
    )
    second_workspace = client.post(
        "/api/v1/workspaces",
        json={"name": "Research B", "module_type": "research"},
        headers=owner_headers,
    )
    assert first_workspace.status_code == 201
    assert second_workspace.status_code == 201

    owner_list_response = client.get("/api/v1/workspaces", headers=owner_headers)
    assert owner_list_response.status_code == 200
    owner_ids = {item["id"] for item in owner_list_response.json()}
    assert owner_ids == {first_workspace.json()["id"], second_workspace.json()["id"]}

    other_list_response = client.get("/api/v1/workspaces", headers=other_headers)
    assert other_list_response.status_code == 200
    assert other_list_response.json() == []


def test_workspace_access_returns_not_found_for_non_members(client: TestClient) -> None:
    owner_auth = _register_and_login(client, email="owner@example.com", name="Owner")
    other_auth = _register_and_login(client, email="other@example.com", name="Other")

    owner_headers = {"Authorization": f"Bearer {owner_auth['token']}"}
    other_headers = {"Authorization": f"Bearer {other_auth['token']}"}

    create_response = client.post(
        "/api/v1/workspaces",
        json={"name": "Research Demo", "module_type": "research"},
        headers=owner_headers,
    )
    assert create_response.status_code == 201
    workspace_id = create_response.json()["id"]

    other_get_response = client.get(f"/api/v1/workspaces/{workspace_id}", headers=other_headers)
    assert other_get_response.status_code == 404

    other_patch_response = client.patch(
        f"/api/v1/workspaces/{workspace_id}",
        json={"description": "Should fail"},
        headers=other_headers,
    )
    assert other_patch_response.status_code == 404


def test_workspace_module_contract_can_be_switched_with_shared_defaults(client: TestClient) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}

    create_response = client.post(
        "/api/v1/workspaces",
        json={"name": "Research Demo"},
        headers=headers,
    )
    assert create_response.status_code == 201
    workspace_id = create_response.json()["id"]

    patch_response = client.patch(
        f"/api/v1/workspaces/{workspace_id}",
        json={"module_type": "support"},
        headers=headers,
    )
    assert patch_response.status_code == 200

    updated = patch_response.json()
    assert updated["module_type"] == "support"
    assert "type" not in updated
    assert updated["module_config_json"]["entry_task_types"] == [
        "ticket_summary",
        "reply_draft",
    ]
    assert updated["module_config_json"]["result_type"] == "support_case_summary"


def test_workspace_update_accepts_deprecated_type_alias(client: TestClient) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}

    create_response = client.post(
        "/api/v1/workspaces",
        json={"name": "Research Demo", "module_type": "research"},
        headers=headers,
    )
    assert create_response.status_code == 201
    workspace_id = create_response.json()["id"]

    patch_response = client.patch(
        f"/api/v1/workspaces/{workspace_id}",
        json={"type": "job"},
        headers=headers,
    )
    assert patch_response.status_code == 200

    updated = patch_response.json()
    assert updated["module_type"] == "job"
    assert "type" not in updated
    assert updated["module_config_json"]["result_type"] == "job_match_summary"


def test_workspace_rejects_unsupported_module_type(client: TestClient) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}

    create_response = client.post(
        "/api/v1/workspaces",
        json={"name": "Research Demo", "module_type": "sales"},
        headers=headers,
    )
    assert create_response.status_code == 422


def test_public_demo_limits_workspace_creation_per_user(
    client: TestClient,
    monkeypatch,
) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "public_demo_mode", True)
    monkeypatch.setattr(settings, "public_demo_max_workspaces_per_user", 1)

    auth = _register_and_login(client, email="demo-owner@example.com", name="Demo Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}

    first_response = client.post(
        "/api/v1/workspaces",
        json={"name": "First Demo Workspace", "module_type": "research"},
        headers=headers,
    )
    assert first_response.status_code == 201

    second_response = client.post(
        "/api/v1/workspaces",
        json={"name": "Second Demo Workspace", "module_type": "support"},
        headers=headers,
    )
    assert second_response.status_code == 409
    assert "up to 1 workspaces per account" in second_response.json()["detail"]
