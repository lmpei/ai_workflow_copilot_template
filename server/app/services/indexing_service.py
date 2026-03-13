from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urlparse

import httpx

from app.core.config import get_settings
from app.models.document import (
    DOCUMENT_STATUS_FAILED,
    DOCUMENT_STATUS_INDEXED,
    DOCUMENT_STATUS_INDEXING,
    Document,
)
from app.models.document_chunk import DocumentChunk
from app.repositories import document_repository
from app.repositories.document_repository import EmbeddingMappingCreate
from app.schemas.document import DocumentResponse


class DocumentIndexingError(Exception):
    pass


class EmbeddingProvider(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...


class VectorStoreClient(Protocol):
    def upsert_embeddings(
        self,
        *,
        collection_name: str,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, object]],
    ) -> None: ...

    def delete_embeddings(
        self,
        *,
        collection_name: str,
        ids: list[str],
    ) -> None: ...


@dataclass(slots=True)
class OpenAICompatibleEmbeddingProvider:
    api_key: str
    model: str
    base_url: str = "https://api.openai.com/v1"
    provider_name: str = "openai"

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if not self.api_key or self.api_key == "replace_me":
            raise DocumentIndexingError(
                f"{self.provider_name} embedding API key must be configured for document indexing",
            )

        try:
            response = httpx.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "input": texts,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            payload = response.json()
            vectors = [
                item["embedding"]
                for item in sorted(payload["data"], key=lambda item: item["index"])
            ]
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
            raise DocumentIndexingError("Failed to generate embeddings") from error

        if len(vectors) != len(texts):
            raise DocumentIndexingError("Embedding response length did not match chunk count")

        return vectors


@dataclass(slots=True)
class ChromaVectorStore:
    url: str

    def _get_client(self) -> Any:
        try:
            import chromadb
        except ImportError as error:
            raise DocumentIndexingError("Chroma dependency is not installed") from error

        parsed = urlparse(self.url)
        host = parsed.hostname or "localhost"
        if parsed.scheme == "https":
            port = parsed.port or 443
        else:
            port = parsed.port or 8000
        ssl = parsed.scheme == "https"
        return chromadb.HttpClient(host=host, port=port, ssl=ssl)

    def _get_collection(self, collection_name: str) -> Any:
        client = self._get_client()
        try:
            return client.get_or_create_collection(name=collection_name)
        except Exception as error:
            raise DocumentIndexingError("Failed to connect to Chroma collection") from error

    def upsert_embeddings(
        self,
        *,
        collection_name: str,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, object]],
    ) -> None:
        collection = self._get_collection(collection_name)
        try:
            collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
        except Exception as error:
            raise DocumentIndexingError("Failed to write embeddings to Chroma") from error

    def delete_embeddings(
        self,
        *,
        collection_name: str,
        ids: list[str],
    ) -> None:
        if not ids:
            return
        collection = self._get_collection(collection_name)
        try:
            collection.delete(ids=ids)
        except Exception as error:
            raise DocumentIndexingError("Failed to delete stale embeddings from Chroma") from error


def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    if settings.embedding_provider not in {"openai", "qwen"}:
        raise DocumentIndexingError(
            f"Unsupported embedding provider: {settings.embedding_provider}",
        )
    api_key = settings.embedding_api_key
    if api_key == "replace_me" and settings.embedding_provider == "openai":
        api_key = settings.openai_api_key
    return OpenAICompatibleEmbeddingProvider(
        api_key=api_key,
        model=settings.embedding_model,
        base_url=settings.embedding_base_url,
        provider_name=settings.embedding_provider,
    )


def get_vector_store() -> VectorStoreClient:
    settings = get_settings()
    if settings.vector_store_backend != "chroma":
        raise DocumentIndexingError(
            f"Unsupported vector store backend: {settings.vector_store_backend}",
        )
    return ChromaVectorStore(url=settings.chroma_url)


def _build_chunk_metadata(document: Document, chunk: DocumentChunk) -> dict[str, object]:
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


def index_document_embeddings(
    *,
    document_id: str,
    user_id: str,
    embedding_provider: EmbeddingProvider | None = None,
    vector_store: VectorStoreClient | None = None,
) -> DocumentResponse:
    document = document_repository.get_document(document_id=document_id, user_id=user_id)
    if document is None:
        raise DocumentIndexingError("Document not found")

    indexing_started = False
    active_vector_store: VectorStoreClient | None = vector_store
    collection_name = get_settings().chroma_collection_name
    upserted_vector_ids: list[str] = []
    try:
        updated_document = document_repository.update_document_status(
            document_id=document_id,
            next_status=DOCUMENT_STATUS_INDEXING,
        )
        if updated_document is None:
            raise DocumentIndexingError("Document not found")
        indexing_started = True

        chunks = document_repository.list_document_chunks(document_id)
        if not chunks:
            raise DocumentIndexingError("Document has no chunks to index")

        active_embedding_provider = embedding_provider or get_embedding_provider()
        active_vector_store = active_vector_store or get_vector_store()
        settings = get_settings()

        stale_embeddings = document_repository.list_document_embeddings(document_id)
        stale_vector_ids = [embedding.vector_store_id for embedding in stale_embeddings]
        active_vector_store.delete_embeddings(
            collection_name=collection_name,
            ids=stale_vector_ids,
        )

        embeddings = active_embedding_provider.embed_texts([chunk.content for chunk in chunks])
        if len(embeddings) != len(chunks):
            raise DocumentIndexingError("Embedding response length did not match chunk count")

        vector_ids = [chunk.id for chunk in chunks]
        metadatas = [_build_chunk_metadata(document, chunk) for chunk in chunks]
        active_vector_store.upsert_embeddings(
            collection_name=collection_name,
            ids=vector_ids,
            documents=[chunk.content for chunk in chunks],
            embeddings=embeddings,
            metadatas=metadatas,
        )
        upserted_vector_ids = vector_ids

        document_repository.replace_document_embeddings(
            document_id,
            [
                EmbeddingMappingCreate(
                    document_chunk_id=chunk.id,
                    vector_store_id=chunk.id,
                    collection_name=collection_name,
                    embedding_model=settings.embedding_model,
                )
                for chunk in chunks
            ],
        )

        updated_document = document_repository.update_document_status(
            document_id=document_id,
            next_status=DOCUMENT_STATUS_INDEXED,
        )
        if updated_document is None:
            raise DocumentIndexingError("Document not found")
        return DocumentResponse.from_model(updated_document)
    except (DocumentIndexingError, ValueError):
        if active_vector_store is not None and upserted_vector_ids:
            try:
                active_vector_store.delete_embeddings(
                    collection_name=collection_name,
                    ids=upserted_vector_ids,
                )
            except DocumentIndexingError:
                pass
        if indexing_started:
            document_repository.update_document_status(
                document_id=document_id,
                next_status=DOCUMENT_STATUS_FAILED,
            )
        raise
