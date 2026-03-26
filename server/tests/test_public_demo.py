import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.services import document_service

UPLOAD_ROOT = Path("storage") / "uploads"


class FakeEmbeddingProvider:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[float(index), float(index + 1)] for index, _ in enumerate(texts)]


class FakeVectorStore:
    def __init__(self) -> None:
        self.upserts: list[dict[str, object]] = []

    def delete_embeddings(self, *, collection_name: str, ids: list[str]) -> None:
        return None

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
                "metadatas": list(metadatas),
            },
        )


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


def setup_function() -> None:
    shutil.rmtree(UPLOAD_ROOT, ignore_errors=True)


def teardown_function() -> None:
    shutil.rmtree(UPLOAD_ROOT, ignore_errors=True)


def test_public_demo_templates_are_listed_without_auth(client: TestClient) -> None:
    response = client.get("/api/v1/public-demo/templates")

    assert response.status_code == 200
    templates = response.json()
    assert [template["template_id"] for template in templates] == ["research", "support", "job"]
    assert templates[0]["showcase_steps"][0]["route_suffix"] == "/documents"


def test_public_demo_template_workspace_creation_seeds_documents(
    client: TestClient,
    monkeypatch,
) -> None:
    auth = _register_and_login(client, email="demo-user@example.com", name="Demo User")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    provider = FakeEmbeddingProvider()
    vector_store = FakeVectorStore()
    monkeypatch.setattr(document_service, "get_embedding_provider", lambda: provider)
    monkeypatch.setattr(document_service, "get_vector_store", lambda: vector_store)

    response = client.post("/api/v1/public-demo/templates/support/workspaces", headers=headers)

    assert response.status_code == 201
    payload = response.json()
    assert payload["workspace"]["module_type"] == "support"
    assert payload["workspace"]["module_config_json"]["guided_demo"] is True
    assert payload["workspace"]["module_config_json"]["demo_template_id"] == "support"
    assert len(payload["documents"]) == 3
    assert all(document["status"] == "indexed" for document in payload["documents"])
    assert all(document["source_type"] == "demo_seed" for document in payload["documents"])
    assert len(vector_store.upserts) == 3

    workspace_list_response = client.get("/api/v1/workspaces", headers=headers)
    assert workspace_list_response.status_code == 200
    assert len(workspace_list_response.json()) == 1


def test_public_demo_template_creation_checks_document_limits_before_workspace_creation(
    client: TestClient,
    monkeypatch,
) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "public_demo_mode", True)
    monkeypatch.setattr(settings, "public_demo_max_documents_per_workspace", 2)

    auth = _register_and_login(client, email="demo-limit@example.com", name="Demo Limit")
    headers = {"Authorization": f"Bearer {auth['token']}"}

    response = client.post("/api/v1/public-demo/templates/research/workspaces", headers=headers)

    assert response.status_code == 409
    assert "needs 3 seeded documents" in response.json()["detail"]

    workspace_list_response = client.get("/api/v1/workspaces", headers=headers)
    assert workspace_list_response.status_code == 200
    assert workspace_list_response.json() == []
