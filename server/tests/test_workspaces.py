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
    assert created["type"] == "research"
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
        json={"name": "Research A", "type": "research"},
        headers=owner_headers,
    )
    second_workspace = client.post(
        "/api/v1/workspaces",
        json={"name": "Research B", "type": "research"},
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
        json={"name": "Research Demo", "type": "research"},
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
