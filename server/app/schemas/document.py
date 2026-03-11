from datetime import datetime
from typing import Literal, TypeAlias, cast

from pydantic import BaseModel

from app.models.document import Document, is_valid_document_status

DocumentStatus: TypeAlias = Literal[
    "uploaded",
    "parsing",
    "chunked",
    "indexing",
    "indexed",
    "failed",
]


class DocumentResponse(BaseModel):
    id: str
    workspace_id: str
    title: str
    source_type: str
    file_path: str | None = None
    mime_type: str | None = None
    status: DocumentStatus
    created_by: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, document: Document) -> "DocumentResponse":
        if not is_valid_document_status(document.status):
            raise ValueError(f"Unsupported document status on model: {document.status}")

        return cls(
            id=document.id,
            workspace_id=document.workspace_id,
            title=document.title,
            source_type=document.source_type,
            file_path=document.file_path,
            mime_type=document.mime_type,
            status=cast(DocumentStatus, document.status),
            created_by=document.created_by,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )
