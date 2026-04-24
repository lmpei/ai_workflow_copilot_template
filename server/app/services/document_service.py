from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.models.document import (
    DOCUMENT_STATUS_CHUNKED,
    DOCUMENT_STATUS_FAILED,
    DOCUMENT_STATUS_INDEXED,
    DOCUMENT_STATUS_PARSING,
)
from app.repositories import document_repository
from app.schemas.document import DocumentResponse
from app.services import document_parsing_service, document_reindex_service
from app.services.document_parsing_service import (
    DocumentProcessingError,
    DocumentUploadError,
    ParsedDocumentSegment,
)
from app.services.document_reindex_service import DocumentAccessError
from app.services.indexing_service import (
    DocumentIndexingError,
    EmbeddingProvider,
    VectorStoreClient,
    get_embedding_provider,
    get_vector_store,
    index_document_embeddings,
)

UPLOAD_ROOT = Path("storage") / "uploads"

_sanitize_filename = document_parsing_service.sanitize_filename
_resolve_document_path = document_parsing_service.resolve_document_path
_parse_text_segments = document_parsing_service.parse_text_segments
_parse_pdf_segments = document_parsing_service.parse_pdf_segments
_build_document_chunks = document_parsing_service.build_document_chunks
_mark_document_failed = document_reindex_service.mark_document_failed
_delete_stale_vectors = document_reindex_service.clear_stale_vectors


def _parse_document_segments(
    *,
    file_path: Path,
    mime_type: str | None,
) -> list[ParsedDocumentSegment]:
    return document_parsing_service.parse_document_segments(
        file_path=file_path,
        mime_type=mime_type,
        parse_text_segments_fn=_parse_text_segments,
        parse_pdf_segments_fn=_parse_pdf_segments,
    )


def ingest_document(
    *,
    document_id: str,
    user_id: str,
    reset_for_reindex: bool = False,
    embedding_provider: EmbeddingProvider | None = None,
    vector_store: VectorStoreClient | None = None,
) -> DocumentResponse:
    document = document_repository.get_document(document_id=document_id, user_id=user_id)
    if document is None:
        raise DocumentAccessError("未找到文档")

    preserve_existing_index = reset_for_reindex and document.status == DOCUMENT_STATUS_INDEXED

    try:
        active_embedding_provider = embedding_provider or get_embedding_provider()
        active_vector_store = vector_store or get_vector_store()

        if preserve_existing_index:
            document_path = _resolve_document_path(document.file_path)
            segments = _parse_document_segments(file_path=document_path, mime_type=document.mime_type)
            chunk_creates = _build_document_chunks(segments)
            replaced_document = document_reindex_service.reindex_document_preserving_existing_index(
                document=document,
                chunk_creates=chunk_creates,
                embedding_provider=active_embedding_provider,
                vector_store=active_vector_store,
            )
            return DocumentResponse.from_model(replaced_document)

        if reset_for_reindex:
            _delete_stale_vectors(document_id=document_id, vector_store=active_vector_store)
            document_repository.clear_document_derived_state(document_id)

        parse_document_into_chunks(document_id=document_id, user_id=user_id)
        return index_document_embeddings(
            document_id=document_id,
            user_id=user_id,
            embedding_provider=active_embedding_provider,
            vector_store=active_vector_store,
        )
    except DocumentAccessError:
        raise
    except (DocumentProcessingError, DocumentIndexingError):
        if preserve_existing_index:
            raise
        _mark_document_failed(document_id)
        raise
    except Exception as error:
        if preserve_existing_index:
            raise DocumentProcessingError(f"文档入库失败：{error}") from error
        _mark_document_failed(document_id)
        raise DocumentProcessingError(f"文档入库失败：{error}") from error


async def upload_document(
    *,
    workspace_id: str,
    user_id: str,
    file: UploadFile,
) -> DocumentResponse:
    has_access = document_repository.user_has_workspace_access(
        workspace_id=workspace_id,
        user_id=user_id,
    )
    if not has_access:
        raise DocumentAccessError("未找到工作区")

    filename = _sanitize_filename(file.filename)
    content = await file.read()
    if not content:
        raise DocumentUploadError("上传文件不能为空")

    document_id = str(uuid4())
    relative_path = Path("uploads") / workspace_id / document_id / filename
    full_path = UPLOAD_ROOT / workspace_id / document_id / filename
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_bytes(content)

    try:
        document = document_repository.create_document(
            document_id=document_id,
            workspace_id=workspace_id,
            title=filename,
            file_path=relative_path.as_posix(),
            mime_type=file.content_type,
            created_by=user_id,
        )
    except Exception:
        full_path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

    return ingest_document(document_id=document.id, user_id=user_id)


def create_text_document(
    *,
    workspace_id: str,
    user_id: str,
    title: str,
    text_content: str,
    source_type: str = "seed",
    embedding_provider: EmbeddingProvider | None = None,
    vector_store: VectorStoreClient | None = None,
) -> DocumentResponse:
    has_access = document_repository.user_has_workspace_access(
        workspace_id=workspace_id,
        user_id=user_id,
    )
    if not has_access:
        raise DocumentAccessError("未找到工作区")

    normalized_text = text_content.strip()
    if not normalized_text:
        raise DocumentUploadError("预置文档内容不能为空")

    filename = _sanitize_filename(title if title.lower().endswith(".txt") else f"{title}.txt")

    document_id = str(uuid4())
    relative_path = Path("uploads") / workspace_id / document_id / filename
    full_path = UPLOAD_ROOT / workspace_id / document_id / filename
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(normalized_text, encoding="utf-8")

    try:
        document = document_repository.create_document(
            document_id=document_id,
            workspace_id=workspace_id,
            title=filename,
            file_path=relative_path.as_posix(),
            mime_type="text/plain",
            created_by=user_id,
            source_type=source_type,
        )
    except Exception:
        full_path.unlink(missing_ok=True)
        raise

    return ingest_document(
        document_id=document.id,
        user_id=user_id,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )


def list_documents(*, workspace_id: str, user_id: str) -> list[DocumentResponse]:
    has_access = document_repository.user_has_workspace_access(
        workspace_id=workspace_id,
        user_id=user_id,
    )
    if not has_access:
        raise DocumentAccessError("未找到工作区")

    documents = document_repository.list_documents(workspace_id=workspace_id, user_id=user_id)
    return [DocumentResponse.from_model(document) for document in documents]


def get_document(*, document_id: str, user_id: str) -> DocumentResponse | None:
    document = document_repository.get_document(document_id=document_id, user_id=user_id)
    if document is None:
        return None
    return DocumentResponse.from_model(document)


def reindex_document(*, document_id: str, user_id: str) -> DocumentResponse | None:
    document = document_repository.get_document(document_id=document_id, user_id=user_id)
    if document is None:
        return None
    return ingest_document(document_id=document_id, user_id=user_id, reset_for_reindex=True)


def parse_document_into_chunks(*, document_id: str, user_id: str) -> DocumentResponse:
    document = document_repository.get_document(document_id=document_id, user_id=user_id)
    if document is None:
        raise DocumentAccessError("未找到文档")

    document_path = _resolve_document_path(document.file_path)
    parsing_started = False

    try:
        parsed_document = document_repository.update_document_status(
            document_id=document_id,
            next_status=DOCUMENT_STATUS_PARSING,
        )
        if parsed_document is None:
            raise DocumentAccessError("未找到文档")
        parsing_started = True

        segments = _parse_document_segments(file_path=document_path, mime_type=document.mime_type)
        chunks = _build_document_chunks(segments)
        document_repository.replace_document_chunks(document_id=document_id, chunks=chunks)

        parsed_document = document_repository.update_document_status(
            document_id=document_id,
            next_status=DOCUMENT_STATUS_CHUNKED,
        )
        if parsed_document is None:
            raise DocumentAccessError("未找到文档")
        return DocumentResponse.from_model(parsed_document)
    except DocumentProcessingError:
        if parsing_started:
            document_repository.update_document_status(
                document_id=document_id,
                next_status=DOCUMENT_STATUS_FAILED,
            )
        raise
    except ValueError as error:
        if parsing_started:
            document_repository.update_document_status(
                document_id=document_id,
                next_status=DOCUMENT_STATUS_FAILED,
            )
            raise DocumentProcessingError(str(error)) from error
        raise DocumentProcessingError(str(error)) from error
