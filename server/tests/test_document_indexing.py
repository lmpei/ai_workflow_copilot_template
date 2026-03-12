from uuid import uuid4

import pytest

from app.core.database import reset_database_for_tests
from app.repositories.document_repository import (
    DocumentChunkCreate,
    create_document,
    list_document_embeddings,
    replace_document_chunks,
    update_document_status,
)
from app.repositories.user_repository import create_user
from app.repositories.workspace_repository import create_workspace
from app.schemas.workspace import WorkspaceCreate
from app.services.indexing_service import DocumentIndexingError, index_document_embeddings


class FakeEmbeddingProvider:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[list[str]] = []

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(texts)
        if self.fail:
            raise DocumentIndexingError("Failed to generate embeddings")
        return [[float(index), float(index + 1)] for index, _ in enumerate(texts)]


class FakeVectorStore:
    def __init__(self, *, fail_on_upsert: bool = False) -> None:
        self.fail_on_upsert = fail_on_upsert
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
        if self.fail_on_upsert:
            raise DocumentIndexingError("Failed to write embeddings to Chroma")
        self.upserts.append(
            {
                "collection_name": collection_name,
                "ids": list(ids),
                "documents": list(documents),
                "embeddings": [list(vector) for vector in embeddings],
                "metadatas": list(metadatas),
            },
        )


@pytest.fixture(autouse=True)
def reset_database() -> None:
    reset_database_for_tests()


def _create_chunked_document_fixture() -> tuple[str, str]:
    unique_suffix = uuid4().hex
    user = create_user(
        email=f"index-owner-{unique_suffix}@example.com",
        password_hash="not-used-in-this-test",
        name="Index Owner",
    )
    workspace = create_workspace(
        WorkspaceCreate(name="Index Workspace", type="research"),
        owner_id=user.id,
    )
    document = create_document(
        document_id=str(uuid4()),
        workspace_id=workspace.id,
        title="index-note.txt",
        file_path="uploads/index-note.txt",
        mime_type="text/plain",
        created_by=user.id,
    )
    update_document_status(document.id, "parsing")
    replace_document_chunks(
        document.id,
        [
            DocumentChunkCreate(
                chunk_index=0,
                content="first indexed chunk",
                token_count=3,
                metadata_json={"char_start": 0, "char_end": 19},
            ),
            DocumentChunkCreate(
                chunk_index=1,
                content="second indexed chunk",
                token_count=3,
                metadata_json={"char_start": 20, "char_end": 40, "page_number": 2},
            ),
        ],
    )
    update_document_status(document.id, "chunked")
    return user.id, document.id


def test_index_document_embeddings_persists_mappings_and_chroma_metadata() -> None:
    user_id, document_id = _create_chunked_document_fixture()
    provider = FakeEmbeddingProvider()
    vector_store = FakeVectorStore()

    indexed_document = index_document_embeddings(
        document_id=document_id,
        user_id=user_id,
        embedding_provider=provider,
        vector_store=vector_store,
    )

    persisted_embeddings = list_document_embeddings(document_id)
    assert indexed_document.status == "indexed"
    assert provider.calls == [["first indexed chunk", "second indexed chunk"]]
    assert len(vector_store.upserts) == 1
    assert vector_store.upserts[0]["collection_name"] == "workspace_documents"
    assert vector_store.upserts[0]["metadatas"][0]["workspace_id"] == indexed_document.workspace_id
    assert vector_store.upserts[0]["metadatas"][1]["page_number"] == 2
    assert len(persisted_embeddings) == 2
    assert [embedding.vector_store_id for embedding in persisted_embeddings] == (
        vector_store.upserts[0]["ids"]
    )


def test_index_document_embeddings_replaces_stale_vector_mappings() -> None:
    user_id, document_id = _create_chunked_document_fixture()
    provider = FakeEmbeddingProvider()
    vector_store = FakeVectorStore()

    first_indexed = index_document_embeddings(
        document_id=document_id,
        user_id=user_id,
        embedding_provider=provider,
        vector_store=vector_store,
    )
    second_indexed = index_document_embeddings(
        document_id=document_id,
        user_id=user_id,
        embedding_provider=provider,
        vector_store=vector_store,
    )

    persisted_embeddings = list_document_embeddings(document_id)
    assert first_indexed.status == "indexed"
    assert second_indexed.status == "indexed"
    assert vector_store.deleted[0]["ids"] == []
    assert vector_store.deleted[1]["ids"] == vector_store.upserts[0]["ids"]
    assert len(persisted_embeddings) == 2


def test_index_document_embeddings_marks_failed_on_provider_or_store_errors() -> None:
    user_id, document_id = _create_chunked_document_fixture()
    provider = FakeEmbeddingProvider(fail=True)
    vector_store = FakeVectorStore()

    with pytest.raises(DocumentIndexingError, match="Failed to generate embeddings"):
        index_document_embeddings(
            document_id=document_id,
            user_id=user_id,
            embedding_provider=provider,
            vector_store=vector_store,
        )

    failed_embeddings = list_document_embeddings(document_id)
    assert failed_embeddings == []

    user_id, document_id = _create_chunked_document_fixture()
    provider = FakeEmbeddingProvider()
    failing_store = FakeVectorStore(fail_on_upsert=True)

    with pytest.raises(DocumentIndexingError, match="Failed to write embeddings to Chroma"):
        index_document_embeddings(
            document_id=document_id,
            user_id=user_id,
            embedding_provider=provider,
            vector_store=failing_store,
        )
