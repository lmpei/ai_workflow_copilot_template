from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import delete, select

from app.core.database import session_scope
from app.models.document import (
    DOCUMENT_STATUS_UPLOADED,
    Document,
    can_transition_document_status,
    is_valid_document_status,
)
from app.models.document_chunk import DocumentChunk
from app.models.embedding import Embedding
from app.models.workspace_member import WorkspaceMember


@dataclass(slots=True)
class DocumentChunkCreate:
    chunk_index: int
    content: str
    token_count: int = 0
    metadata_json: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class EmbeddingMappingCreate:
    document_chunk_id: str
    vector_store_id: str
    collection_name: str
    embedding_model: str


def user_has_workspace_access(workspace_id: str, user_id: str) -> bool:
    with session_scope() as session:
        statement = select(WorkspaceMember.id).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        return session.scalar(statement) is not None


def create_document(
    *,
    document_id: str,
    workspace_id: str,
    title: str,
    file_path: str,
    mime_type: str | None,
    created_by: str,
    source_type: str = "upload",
    status: str = DOCUMENT_STATUS_UPLOADED,
) -> Document:
    if not is_valid_document_status(status):
        raise ValueError(f"Unsupported document status: {status}")

    now = datetime.now(UTC)
    document = Document(
        id=document_id,
        workspace_id=workspace_id,
        title=title,
        source_type=source_type,
        file_path=file_path,
        mime_type=mime_type,
        status=status,
        created_by=created_by,
        created_at=now,
        updated_at=now,
    )
    with session_scope() as session:
        session.add(document)
        session.flush()
        session.refresh(document)
        return document


def list_documents(workspace_id: str, user_id: str) -> list[Document]:
    with session_scope() as session:
        statement = (
            select(Document)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Document.workspace_id)
            .where(
                Document.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
            .order_by(Document.created_at.asc())
        )
        result = session.scalars(statement)
        return list(result)


def get_document(document_id: str, user_id: str) -> Document | None:
    with session_scope() as session:
        statement = (
            select(Document)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Document.workspace_id)
            .where(
                Document.id == document_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        return session.scalar(statement)


def reindex_document(document_id: str, user_id: str) -> Document | None:
    with session_scope() as session:
        statement = (
            select(Document)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Document.workspace_id)
            .where(
                Document.id == document_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        document = session.scalar(statement)
        if document is None:
            return None

        document.status = DOCUMENT_STATUS_UPLOADED
        document.updated_at = datetime.now(UTC)
        session.add(document)
        session.flush()
        session.refresh(document)
        return document


def list_document_chunks(document_id: str) -> list[DocumentChunk]:
    with session_scope() as session:
        statement = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
        )
        return list(session.scalars(statement))


def replace_document_chunks(
    document_id: str,
    chunks: list[DocumentChunkCreate],
) -> list[DocumentChunk]:
    with session_scope() as session:
        existing_chunk_ids = list(
            session.scalars(
                select(DocumentChunk.id).where(DocumentChunk.document_id == document_id),
            ),
        )
        if existing_chunk_ids:
            session.execute(
                delete(Embedding).where(Embedding.document_chunk_id.in_(existing_chunk_ids)),
            )
        session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))

        created_chunks = [
            DocumentChunk(
                id=str(uuid4()),
                document_id=document_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                token_count=chunk.token_count,
                metadata_json=chunk.metadata_json,
            )
            for chunk in chunks
        ]
        session.add_all(created_chunks)
        session.flush()
        for chunk in created_chunks:
            session.refresh(chunk)
        return created_chunks


def list_document_embeddings(document_id: str) -> list[Embedding]:
    with session_scope() as session:
        statement = (
            select(Embedding)
            .join(DocumentChunk, DocumentChunk.id == Embedding.document_chunk_id)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc(), Embedding.created_at.asc())
        )
        return list(session.scalars(statement))


def replace_document_embeddings(
    document_id: str,
    embeddings: list[EmbeddingMappingCreate],
) -> list[Embedding]:
    with session_scope() as session:
        chunk_ids = list(
            session.scalars(
                select(DocumentChunk.id).where(DocumentChunk.document_id == document_id),
            ),
        )
        chunk_id_set = set(chunk_ids)
        if chunk_ids:
            session.execute(
                delete(Embedding).where(Embedding.document_chunk_id.in_(chunk_ids)),
            )
        invalid_chunk_ids = [
            embedding.document_chunk_id
            for embedding in embeddings
            if embedding.document_chunk_id not in chunk_id_set
        ]
        if invalid_chunk_ids:
            raise ValueError("Embedding mappings must reference chunks for the target document")

        created_embeddings = [
            Embedding(
                id=str(uuid4()),
                document_chunk_id=embedding.document_chunk_id,
                vector_store_id=embedding.vector_store_id,
                collection_name=embedding.collection_name,
                embedding_model=embedding.embedding_model,
            )
            for embedding in embeddings
        ]
        session.add_all(created_embeddings)
        session.flush()
        for embedding in created_embeddings:
            session.refresh(embedding)
        return created_embeddings


def update_document_status(document_id: str, next_status: str) -> Document | None:
    if not is_valid_document_status(next_status):
        raise ValueError(f"Unsupported document status: {next_status}")

    with session_scope() as session:
        document = session.get(Document, document_id)
        if document is None:
            return None

        if not can_transition_document_status(document.status, next_status):
            raise ValueError(
                f"Invalid document status transition: {document.status} -> {next_status}",
            )

        document.status = next_status
        document.updated_at = datetime.now(UTC)
        session.add(document)
        session.flush()
        session.refresh(document)
        return document
