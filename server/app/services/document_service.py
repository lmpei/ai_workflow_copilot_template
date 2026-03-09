from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.repositories import document_repository
from app.schemas.document import DocumentResponse

UPLOAD_ROOT = Path("storage") / "uploads"


class DocumentAccessError(Exception):
    pass


class DocumentUploadError(Exception):
    pass


def _sanitize_filename(filename: str | None) -> str:
    if filename is None:
        raise DocumentUploadError("Uploaded file must include a filename")

    cleaned_name = filename.replace("\\", "/").split("/")[-1]
    if not cleaned_name or cleaned_name in {".", ".."}:
        raise DocumentUploadError("Uploaded file must include a filename")
    return cleaned_name


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
        raise DocumentAccessError("Workspace not found")

    filename = _sanitize_filename(file.filename)
    content = await file.read()
    if not content:
        raise DocumentUploadError("Uploaded file cannot be empty")

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

    return DocumentResponse.from_model(document)


def list_documents(*, workspace_id: str, user_id: str) -> list[DocumentResponse]:
    has_access = document_repository.user_has_workspace_access(
        workspace_id=workspace_id,
        user_id=user_id,
    )
    if not has_access:
        raise DocumentAccessError("Workspace not found")

    documents = document_repository.list_documents(workspace_id=workspace_id, user_id=user_id)
    return [DocumentResponse.from_model(document) for document in documents]


def get_document(*, document_id: str, user_id: str) -> DocumentResponse | None:
    document = document_repository.get_document(document_id=document_id, user_id=user_id)
    if document is None:
        return None
    return DocumentResponse.from_model(document)


def reindex_document(*, document_id: str, user_id: str) -> DocumentResponse | None:
    document = document_repository.reindex_document(document_id=document_id, user_id=user_id)
    if document is None:
        return None
    return DocumentResponse.from_model(document)
