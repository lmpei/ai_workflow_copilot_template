import shutil
from pathlib import Path

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.repositories.document_repository import list_document_chunks, list_document_embeddings
from app.services import document_service
from app.services.indexing_service import DocumentIndexingError

UPLOAD_ROOT = Path("storage") / "uploads"


class FakeEmbeddingProvider:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[list[str]] = []

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        if self.fail:
            raise DocumentIndexingError("Failed to generate embeddings")
        return [[float(index), float(index + 1)] for index, _ in enumerate(texts)]


class FakeVectorStore:
    def __init__(self) -> None:
        self.deleted: list[dict[str, object]] = []
        self.upserts: list[dict[str, object]] = []

    def delete_embeddings(self, *, collection_name: str, ids: list[str]) -> None:
        self.deleted.append({"collection_name": collection_name, "ids": list(ids)})

    def upsert_embeddings(
        self,
        *,
        collection_name: str,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, object]],
    ) -> None:
        self.upserts.append(
            {
                "collection_name": collection_name,
                "ids": list(ids),
                "documents": list(documents),
                "embeddings": [list(vector) for vector in embeddings],
                "metadatas": list(metadatas),
            },
        )


def _patch_ingest_dependencies(
    monkeypatch: MonkeyPatch,
    *,
    provider: FakeEmbeddingProvider,
    vector_store: FakeVectorStore,
) -> None:
    monkeypatch.setattr(document_service, "get_embedding_provider", lambda: provider)
    monkeypatch.setattr(document_service, "get_vector_store", lambda: vector_store)


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


def test_document_upload_list_get_and_reindex(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])
    provider = FakeEmbeddingProvider()
    vector_store = FakeVectorStore()
    _patch_ingest_dependencies(
        monkeypatch,
        provider=provider,
        vector_store=vector_store,
    )

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
    assert uploaded["status"] == "indexed"
    assert uploaded["file_path"].startswith(f"uploads/{workspace_id}/")
    assert provider.calls == [["phase 1 document body"]]
    assert len(vector_store.upserts) == 1
    assert len(list_document_chunks(uploaded["id"])) == 1
    assert len(list_document_embeddings(uploaded["id"])) == 1

    list_response = client.get(f"/api/v1/workspaces/{workspace_id}/documents", headers=headers)
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [uploaded["id"]]

    detail_response = client.get(f"/api/v1/documents/{uploaded['id']}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == uploaded["id"]

    document_path = Path("storage") / uploaded["file_path"]
    document_path.write_text("phase 2 document body", encoding="utf-8")
    previous_chunk_ids = [chunk.id for chunk in list_document_chunks(uploaded["id"])]
    previous_embeddings = list_document_embeddings(uploaded["id"])
    previous_vector_ids = [embedding.vector_store_id for embedding in previous_embeddings]

    reindex_response = client.post(f"/api/v1/documents/{uploaded['id']}/reindex", headers=headers)
    assert reindex_response.status_code == 200
    assert reindex_response.json()["status"] == "indexed"
    assert provider.calls[-1] == ["phase 2 document body"]
    refreshed_chunk_ids = [chunk.id for chunk in list_document_chunks(uploaded["id"])]
    refreshed_vector_ids = [
        embedding.vector_store_id for embedding in list_document_embeddings(uploaded["id"])
    ]
    assert refreshed_chunk_ids != previous_chunk_ids
    assert refreshed_vector_ids == refreshed_chunk_ids
    assert previous_vector_ids in [entry["ids"] for entry in vector_store.deleted]


def test_document_uploads_with_same_filename_do_not_collide(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])
    provider = FakeEmbeddingProvider()
    vector_store = FakeVectorStore()
    _patch_ingest_dependencies(monkeypatch, provider=provider, vector_store=vector_store)

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


def test_document_upload_failure_marks_failed_and_returns_error(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])
    provider = FakeEmbeddingProvider(fail=True)
    vector_store = FakeVectorStore()
    _patch_ingest_dependencies(
        monkeypatch,
        provider=provider,
        vector_store=vector_store,
    )

    upload_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
        headers=headers,
        files={"file": ("failure.txt", b"index me", "text/plain")},
    )

    assert upload_response.status_code == 500
    assert upload_response.json()["detail"] == "Failed to generate embeddings"

    list_response = client.get(f"/api/v1/workspaces/{workspace_id}/documents", headers=headers)
    assert list_response.status_code == 200
    documents = list_response.json()
    assert len(documents) == 1
    assert documents[0]["status"] == "failed"

    document_id = documents[0]["id"]
    assert len(list_document_embeddings(document_id)) == 0
