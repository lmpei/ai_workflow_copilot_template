from dataclasses import dataclass
from uuid import uuid4

from app.core.config import get_settings
from app.models.document import (
    DOCUMENT_STATUS_FAILED,
    DOCUMENT_STATUS_INDEXED,
    DOCUMENT_STATUS_INDEXING,
    Document,
)
from app.repositories import document_repository
from app.repositories.document_repository import (
    DocumentChunkCreate,
    DocumentChunkReplace,
    EmbeddingMappingCreate,
)
from app.services.document_parsing_service import DocumentProcessingError
from app.services.indexing_service import (
    DocumentIndexingError,
    EmbeddingProvider,
    VectorStoreClient,
)


class DocumentAccessError(Exception):
    pass


@dataclass(slots=True)
class PreparedDocumentChunk:
    id: str
    chunk_index: int
    content: str
    token_count: int
    metadata_json: dict[str, object]


def mark_document_failed(document_id: str) -> None:
    try:
        document_repository.update_document_status(
            document_id=document_id,
            next_status=DOCUMENT_STATUS_FAILED,
        )
    except ValueError:
        pass


def clear_stale_vectors(*, document_id: str, vector_store: VectorStoreClient) -> None:
    stale_embeddings = document_repository.list_document_embeddings(document_id)
    stale_vector_ids = [embedding.vector_store_id for embedding in stale_embeddings]
    if not stale_vector_ids:
        return

    vector_store.delete_embeddings(
        collection_name=get_settings().chroma_collection_name,
        ids=stale_vector_ids,
    )


def build_prepared_chunks(chunk_creates: list[DocumentChunkCreate]) -> list[PreparedDocumentChunk]:
    return [
        PreparedDocumentChunk(
            id=str(uuid4()),
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            token_count=chunk.token_count,
            metadata_json=chunk.metadata_json,
        )
        for chunk in chunk_creates
    ]


def build_chunk_metadata(document, chunk: PreparedDocumentChunk) -> dict[str, object]:
    metadata: dict[str, object] = {
        "workspace_id": document.workspace_id,
        "document_id": document.id,
        "chunk_id": chunk.id,
        "chunk_index": chunk.chunk_index,
        "document_title": document.title,
        "mime_type": document.mime_type or "",
        "source_type": document.source_type,
    }
    page_number = chunk.metadata_json.get("page_number")
    if isinstance(page_number, int):
        metadata["page_number"] = page_number
    return metadata


def restore_document_status(document_id: str, previous_status: str) -> None:
    if previous_status not in {DOCUMENT_STATUS_INDEXED, DOCUMENT_STATUS_FAILED}:
        mark_document_failed(document_id)
        return

    try:
        document_repository.update_document_status(
            document_id=document_id,
            next_status=previous_status,
        )
    except ValueError:
        mark_document_failed(document_id)


def reindex_document_preserving_existing_index(
    *,
    document: Document,
    chunk_creates: list[DocumentChunkCreate],
    embedding_provider: EmbeddingProvider,
    vector_store: VectorStoreClient,
) -> Document:
    previous_status = document.status
    current_embeddings = document_repository.list_document_embeddings(document.id)
    current_vector_ids = [embedding.vector_store_id for embedding in current_embeddings]
    collection_name = get_settings().chroma_collection_name
    embedding_model = get_settings().embedding_model

    indexing_document = document_repository.update_document_status(
        document_id=document.id,
        next_status=DOCUMENT_STATUS_INDEXING,
    )
    if indexing_document is None:
        raise DocumentAccessError("Document not found")

    upserted_vector_ids: list[str] = []
    try:
        prepared_chunks = build_prepared_chunks(chunk_creates)
        embeddings = embedding_provider.embed_texts([chunk.content for chunk in prepared_chunks])
        if len(embeddings) != len(prepared_chunks):
            raise DocumentIndexingError("Embedding response length did not match chunk count")

        upserted_vector_ids = [chunk.id for chunk in prepared_chunks]
        vector_store.upsert_embeddings(
            collection_name=collection_name,
            ids=upserted_vector_ids,
            documents=[chunk.content for chunk in prepared_chunks],
            embeddings=embeddings,
            metadatas=[build_chunk_metadata(document, chunk) for chunk in prepared_chunks],
        )

        replaced_document = document_repository.replace_document_index(
            document.id,
            chunks=[
                DocumentChunkReplace(
                    id=chunk.id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    token_count=chunk.token_count,
                    metadata_json=chunk.metadata_json,
                )
                for chunk in prepared_chunks
            ],
            embeddings=[
                EmbeddingMappingCreate(
                    document_chunk_id=chunk.id,
                    vector_store_id=chunk.id,
                    collection_name=collection_name,
                    embedding_model=embedding_model,
                )
                for chunk in prepared_chunks
            ],
            next_status=DOCUMENT_STATUS_INDEXED,
        )
        if replaced_document is None:
            raise DocumentAccessError("Document not found")
    except DocumentAccessError:
        if upserted_vector_ids:
            try:
                vector_store.delete_embeddings(
                    collection_name=collection_name,
                    ids=upserted_vector_ids,
                )
            except DocumentIndexingError:
                pass
        restore_document_status(document.id, previous_status)
        raise
    except (DocumentProcessingError, DocumentIndexingError, ValueError):
        if upserted_vector_ids:
            try:
                vector_store.delete_embeddings(
                    collection_name=collection_name,
                    ids=upserted_vector_ids,
                )
            except DocumentIndexingError:
                pass
        restore_document_status(document.id, previous_status)
        raise
    except Exception as error:
        if upserted_vector_ids:
            try:
                vector_store.delete_embeddings(
                    collection_name=collection_name,
                    ids=upserted_vector_ids,
                )
            except DocumentIndexingError:
                pass
        restore_document_status(document.id, previous_status)
        raise DocumentProcessingError(f"Document ingest failed: {error}") from error

    if current_vector_ids:
        try:
            vector_store.delete_embeddings(
                collection_name=collection_name,
                ids=current_vector_ids,
            )
        except DocumentIndexingError:
            pass

    return replaced_document
