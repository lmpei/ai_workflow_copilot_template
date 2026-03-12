import re
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.models.document import (
    DOCUMENT_STATUS_CHUNKED,
    DOCUMENT_STATUS_FAILED,
    DOCUMENT_STATUS_PARSING,
)
from app.repositories import document_repository
from app.repositories.document_repository import DocumentChunkCreate
from app.schemas.document import DocumentResponse

UPLOAD_ROOT = Path("storage") / "uploads"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MIN_CHUNK_BREAK = 400
SUPPORTED_TEXT_MIME_TYPES = {"text/plain", "text/markdown"}
SUPPORTED_PDF_MIME_TYPE = "application/pdf"


class DocumentAccessError(Exception):
    pass


class DocumentUploadError(Exception):
    pass


class DocumentProcessingError(Exception):
    pass


@dataclass(slots=True)
class ParsedDocumentSegment:
    text: str
    metadata: dict[str, object]


def _sanitize_filename(filename: str | None) -> str:
    if filename is None:
        raise DocumentUploadError("Uploaded file must include a filename")

    cleaned_name = filename.replace("\\", "/").split("/")[-1]
    if not cleaned_name or cleaned_name in {".", ".."}:
        raise DocumentUploadError("Uploaded file must include a filename")
    return cleaned_name


def _resolve_document_path(file_path: str | None) -> Path:
    if not file_path:
        raise DocumentProcessingError("Document file path is missing")

    full_path = Path("storage") / file_path
    if not full_path.exists():
        raise DocumentProcessingError("Document file could not be found on disk")
    return full_path


def _normalize_text(text: str) -> str:
    normalized_lines = [
        re.sub(r"[ \t]+", " ", line).strip()
        for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    ]
    normalized = "\n".join(normalized_lines)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _infer_mime_type(*, mime_type: str | None, file_path: Path) -> str:
    if mime_type:
        return mime_type

    suffix = file_path.suffix.lower()
    if suffix == ".md":
        return "text/markdown"
    if suffix == ".txt":
        return "text/plain"
    if suffix == ".pdf":
        return SUPPORTED_PDF_MIME_TYPE
    return "application/octet-stream"


def _parse_text_segments(file_path: Path) -> list[ParsedDocumentSegment]:
    try:
        raw_text = file_path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as error:
        raise DocumentProcessingError("Document text encoding is not supported") from error

    normalized = _normalize_text(raw_text)
    if not normalized:
        raise DocumentProcessingError("Document does not contain parseable text")

    return [ParsedDocumentSegment(text=normalized, metadata={})]


def _parse_pdf_segments(file_path: Path) -> list[ParsedDocumentSegment]:
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise DocumentProcessingError("PDF parsing dependency is not installed") from error

    try:
        reader = PdfReader(str(file_path))
        segments = []
        for page_number, page in enumerate(reader.pages, start=1):
            extracted_text = page.extract_text() or ""
            normalized = _normalize_text(extracted_text)
            if normalized:
                segments.append(
                    ParsedDocumentSegment(
                        text=normalized,
                        metadata={"page_number": page_number},
                    ),
                )
    except Exception as error:
        raise DocumentProcessingError("Failed to parse PDF document") from error

    if not segments:
        raise DocumentProcessingError("Document does not contain parseable text")
    return segments


def _parse_document_segments(
    *,
    file_path: Path,
    mime_type: str | None,
) -> list[ParsedDocumentSegment]:
    resolved_mime_type = _infer_mime_type(mime_type=mime_type, file_path=file_path)
    if resolved_mime_type in SUPPORTED_TEXT_MIME_TYPES:
        return _parse_text_segments(file_path)
    if resolved_mime_type == SUPPORTED_PDF_MIME_TYPE:
        return _parse_pdf_segments(file_path)
    raise DocumentProcessingError(f"Unsupported document type: {resolved_mime_type}")


def _build_document_chunks(segments: list[ParsedDocumentSegment]) -> list[DocumentChunkCreate]:
    created_chunks: list[DocumentChunkCreate] = []
    chunk_index = 0

    for segment in segments:
        segment_text = segment.text
        segment_length = len(segment_text)
        start = 0

        while start < segment_length:
            end = min(start + CHUNK_SIZE, segment_length)
            if end < segment_length:
                breakpoint = segment_text.rfind(" ", start + MIN_CHUNK_BREAK, end)
                if breakpoint > start:
                    end = breakpoint

            chunk_text = segment_text[start:end].strip()
            if chunk_text:
                metadata = {
                    **segment.metadata,
                    "char_start": start,
                    "char_end": end,
                }
                created_chunks.append(
                    DocumentChunkCreate(
                        chunk_index=chunk_index,
                        content=chunk_text,
                        token_count=len(chunk_text.split()),
                        metadata_json=metadata,
                    ),
                )
                chunk_index += 1

            if end >= segment_length:
                break

            next_start = max(end - CHUNK_OVERLAP, start + 1)
            while next_start < segment_length and segment_text[next_start].isspace():
                next_start += 1
            start = next_start

    if not created_chunks:
        raise DocumentProcessingError("Document does not contain parseable text")

    return created_chunks


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


def parse_document_into_chunks(*, document_id: str, user_id: str) -> DocumentResponse:
    document = document_repository.get_document(document_id=document_id, user_id=user_id)
    if document is None:
        raise DocumentAccessError("Document not found")

    document_path = _resolve_document_path(document.file_path)
    parsing_started = False

    try:
        parsed_document = document_repository.update_document_status(
            document_id=document_id,
            next_status=DOCUMENT_STATUS_PARSING,
        )
        if parsed_document is None:
            raise DocumentAccessError("Document not found")
        parsing_started = True

        segments = _parse_document_segments(file_path=document_path, mime_type=document.mime_type)
        chunks = _build_document_chunks(segments)
        document_repository.replace_document_chunks(document_id=document_id, chunks=chunks)

        parsed_document = document_repository.update_document_status(
            document_id=document_id,
            next_status=DOCUMENT_STATUS_CHUNKED,
        )
        if parsed_document is None:
            raise DocumentAccessError("Document not found")
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
