from fastapi.testclient import TestClient


def test_workspace_crud(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/workspaces",
        json={"name": "Research Demo", "type": "research", "description": "Initial workspace"},
    )
    assert create_response.status_code == 201

    created = create_response.json()
    workspace_id = created["id"]
    assert created["name"] == "Research Demo"
    assert created["type"] == "research"
    assert created["owner_id"] == "demo-user"

    get_response = client.get(f"/api/v1/workspaces/{workspace_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == workspace_id

    patch_response = client.patch(
        f"/api/v1/workspaces/{workspace_id}",
        json={"description": "Updated description"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["description"] == "Updated description"

    list_response = client.get("/api/v1/workspaces")
    assert list_response.status_code == 200
    assert any(item["id"] == workspace_id for item in list_response.json())
