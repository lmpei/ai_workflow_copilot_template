from uuid import uuid4

import pytest

from app.core.database import reset_database_for_tests
from app.repositories.document_repository import (
    DocumentChunkCreate,
    EmbeddingMappingCreate,
    create_document,
    list_document_chunks,
    list_document_embeddings,
    replace_document_chunks,
    replace_document_embeddings,
    update_document_status,
)
from app.repositories.user_repository import create_user
from app.repositories.workspace_repository import create_workspace
from app.schemas.workspace import WorkspaceCreate


@pytest.fixture(autouse=True)
def reset_database() -> None:
    reset_database_for_tests()


def _create_document_fixture() -> str:
    unique_suffix = uuid4().hex
    user = create_user(
        email=f"repo-owner-{unique_suffix}@example.com",
        password_hash="not-used-in-this-test",
        name="Repository Owner",
    )
    workspace = create_workspace(
        WorkspaceCreate(name="Repository Workspace", type="research"),
        owner_id=user.id,
    )
    document = create_document(
        document_id=str(uuid4()),
        workspace_id=workspace.id,
        title="repo-note.txt",
        file_path="uploads/repo-note.txt",
        mime_type="text/plain",
        created_by=user.id,
    )
    return document.id


def test_document_repository_replaces_chunks_and_embeddings() -> None:
    document_id = _create_document_fixture()

    created_chunks = replace_document_chunks(
        document_id,
        [
            DocumentChunkCreate(
                chunk_index=0,
                content="first chunk",
                token_count=3,
                metadata_json={"char_start": 0, "char_end": 11},
            ),
            DocumentChunkCreate(
                chunk_index=1,
                content="second chunk",
                token_count=4,
                metadata_json={"char_start": 12, "char_end": 24},
            ),
        ],
    )

    persisted_chunks = list_document_chunks(document_id)
    assert [chunk.chunk_index for chunk in persisted_chunks] == [0, 1]
    assert persisted_chunks[0].metadata_json["char_start"] == 0

    created_embeddings = replace_document_embeddings(
        document_id,
        [
            EmbeddingMappingCreate(
                document_chunk_id=created_chunks[0].id,
                vector_store_id="vec-1",
                collection_name="workspace_documents",
                embedding_model="text-embedding-3-small",
            ),
            EmbeddingMappingCreate(
                document_chunk_id=created_chunks[1].id,
                vector_store_id="vec-2",
                collection_name="workspace_documents",
                embedding_model="text-embedding-3-small",
            ),
        ],
    )

    persisted_embeddings = list_document_embeddings(document_id)
    assert len(created_embeddings) == 2
    assert [embedding.vector_store_id for embedding in persisted_embeddings] == ["vec-1", "vec-2"]


def test_document_repository_allows_documents_to_have_zero_chunks() -> None:
    document_id = _create_document_fixture()

    parsing = update_document_status(document_id, "parsing")
    assert parsing is not None
    assert parsing.status == "parsing"

    replace_document_chunks(document_id, [])

    assert list_document_chunks(document_id) == []


def test_document_status_transition_supports_phase_two_lifecycle() -> None:
    document_id = _create_document_fixture()

    parsing = update_document_status(document_id, "parsing")
    assert parsing is not None
    assert parsing.status == "parsing"

    chunked = update_document_status(document_id, "chunked")
    assert chunked is not None
    assert chunked.status == "chunked"

    indexing = update_document_status(document_id, "indexing")
    assert indexing is not None
    assert indexing.status == "indexing"

    indexed = update_document_status(document_id, "indexed")
    assert indexed is not None
    assert indexed.status == "indexed"


def test_document_status_transition_rejects_invalid_state_changes() -> None:
    document_id = _create_document_fixture()

    with pytest.raises(ValueError, match="Invalid document status transition"):
        update_document_status(document_id, "indexed")

    with pytest.raises(ValueError, match="Unsupported document status"):
        update_document_status(document_id, "queued")


def test_document_repository_rejects_embedding_mappings_for_foreign_chunks() -> None:
    first_document_id = _create_document_fixture()
    second_document_id = _create_document_fixture()

    foreign_chunk = replace_document_chunks(
        second_document_id,
        [
            DocumentChunkCreate(
                chunk_index=0,
                content="foreign chunk",
                token_count=2,
            ),
        ],
    )[0]

    with pytest.raises(
        ValueError,
        match="Embedding mappings must reference chunks for the target document",
    ):
        replace_document_embeddings(
            first_document_id,
            [
                EmbeddingMappingCreate(
                    document_chunk_id=foreign_chunk.id,
                    vector_store_id="vec-foreign",
                    collection_name="workspace_documents",
                    embedding_model="text-embedding-3-small",
                ),
            ],
        )
