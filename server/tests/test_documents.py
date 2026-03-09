import shutil
from pathlib import Path

from fastapi.testclient import TestClient

UPLOAD_ROOT = Path("storage") / "uploads"


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


def _create_workspace(client: TestClient, token: str, *, name: str = "Research Demo") -> str:
    response = client.post(
        "/api/v1/workspaces",
        json={"name": name, "type": "research"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def setup_function() -> None:
    shutil.rmtree(UPLOAD_ROOT, ignore_errors=True)


def teardown_function() -> None:
    shutil.rmtree(UPLOAD_ROOT, ignore_errors=True)


def test_document_upload_list_get_and_reindex(client: TestClient) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    upload_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
        headers=headers,
        files={"file": ("nested\\requirements.txt", b"phase 1 document body", "text/plain")},
    )
    assert upload_response.status_code == 201
    uploaded = upload_response.json()
    assert uploaded["workspace_id"] == workspace_id
    assert uploaded["title"] == "requirements.txt"
    assert uploaded["created_by"] == auth["user_id"]
    assert uploaded["status"] == "uploaded"
    assert uploaded["file_path"].startswith(f"uploads/{workspace_id}/")

    list_response = client.get(f"/api/v1/workspaces/{workspace_id}/documents", headers=headers)
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [uploaded["id"]]

    detail_response = client.get(f"/api/v1/documents/{uploaded['id']}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == uploaded["id"]

    reindex_response = client.post(f"/api/v1/documents/{uploaded['id']}/reindex", headers=headers)
    assert reindex_response.status_code == 200
    assert reindex_response.json()["status"] == "uploaded"


def test_document_uploads_with_same_filename_do_not_collide(client: TestClient) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    first_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
        headers=headers,
        files={"file": ("report.txt", b"first body", "text/plain")},
    )
    second_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
        headers=headers,
        files={"file": ("report.txt", b"second body", "text/plain")},
    )
    assert first_response.status_code == 201
    assert second_response.status_code == 201

    first_document = first_response.json()
    second_document = second_response.json()
    assert first_document["file_path"] != second_document["file_path"]


def test_document_upload_rejects_unknown_workspace_empty_file_and_non_member(
    client: TestClient,
) -> None:
    owner_auth = _register_and_login(client, email="owner@example.com", name="Owner")
    other_auth = _register_and_login(client, email="other@example.com", name="Other")
    owner_headers = {"Authorization": f"Bearer {owner_auth['token']}"}
    other_headers = {"Authorization": f"Bearer {other_auth['token']}"}
    workspace_id = _create_workspace(client, owner_auth["token"])

    unknown_workspace_response = client.post(
        "/api/v1/workspaces/unknown-workspace/documents/upload",
        headers=owner_headers,
        files={"file": ("note.txt", b"body", "text/plain")},
    )
    assert unknown_workspace_response.status_code == 404

    empty_file_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
        headers=owner_headers,
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert empty_file_response.status_code == 400

    no_access_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
        headers=other_headers,
        files={"file": ("note.txt", b"body", "text/plain")},
    )
    assert no_access_response.status_code == 404
