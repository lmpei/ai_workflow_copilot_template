import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from app.repositories.document_repository import DocumentChunkCreate

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MIN_CHUNK_BREAK = 400
SUPPORTED_TEXT_MIME_TYPES = {"text/plain", "text/markdown"}
SUPPORTED_PDF_MIME_TYPE = "application/pdf"


class DocumentUploadError(Exception):
    pass


class DocumentProcessingError(Exception):
    pass


@dataclass(slots=True)
class ParsedDocumentSegment:
    text: str
    metadata: dict[str, object]


def sanitize_filename(filename: str | None) -> str:
    if filename is None:
        raise DocumentUploadError("Uploaded file must include a filename")

    cleaned_name = filename.replace("\\", "/").split("/")[-1]
    if not cleaned_name or cleaned_name in {".", ".."}:
        raise DocumentUploadError("Uploaded file must include a filename")
    return cleaned_name


def resolve_document_path(file_path: str | None) -> Path:
    if not file_path:
        raise DocumentProcessingError("Document file path is missing")

    full_path = Path("storage") / file_path
    if not full_path.exists():
        raise DocumentProcessingError("Document file could not be found on disk")
    return full_path


def normalize_text(text: str) -> str:
    normalized_lines = [
        re.sub(r"[ \t]+", " ", line).strip()
        for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    ]
    normalized = "\n".join(normalized_lines)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def infer_mime_type(*, mime_type: str | None, file_path: Path) -> str:
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


def parse_text_segments(file_path: Path) -> list[ParsedDocumentSegment]:
    try:
        raw_text = file_path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as error:
        raise DocumentProcessingError("Document text encoding is not supported") from error

    normalized = normalize_text(raw_text)
    if not normalized:
        raise DocumentProcessingError("Document does not contain parseable text")

    return [ParsedDocumentSegment(text=normalized, metadata={})]


def parse_pdf_segments(file_path: Path) -> list[ParsedDocumentSegment]:
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise DocumentProcessingError("PDF parsing dependency is not installed") from error

    try:
        reader = PdfReader(str(file_path))
        segments = []
        for page_number, page in enumerate(reader.pages, start=1):
            extracted_text = page.extract_text() or ""
            normalized = normalize_text(extracted_text)
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


def parse_document_segments(
    *,
    file_path: Path,
    mime_type: str | None,
    parse_text_segments_fn: Callable[[Path], list[ParsedDocumentSegment]] | None = None,
    parse_pdf_segments_fn: Callable[[Path], list[ParsedDocumentSegment]] | None = None,
) -> list[ParsedDocumentSegment]:
    text_segment_builder = parse_text_segments_fn or parse_text_segments
    pdf_segment_builder = parse_pdf_segments_fn or parse_pdf_segments
    resolved_mime_type = infer_mime_type(mime_type=mime_type, file_path=file_path)
    if resolved_mime_type in SUPPORTED_TEXT_MIME_TYPES:
        return text_segment_builder(file_path)
    if resolved_mime_type == SUPPORTED_PDF_MIME_TYPE:
        return pdf_segment_builder(file_path)
    raise DocumentProcessingError(f"Unsupported document type: {resolved_mime_type}")


def build_document_chunks(segments: list[ParsedDocumentSegment]) -> list[DocumentChunkCreate]:
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
