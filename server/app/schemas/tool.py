from pydantic import BaseModel, Field

from app.schemas.document import DocumentStatus


class SearchDocumentsToolInput(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=4, ge=1, le=4)


class WorkspaceDocumentsToolInput(BaseModel):
    limit: int = Field(default=20, ge=1, le=50)


class GetDocumentToolInput(BaseModel):
    document_id: str


class ToolDocumentSummary(BaseModel):
    id: str
    title: str
    status: DocumentStatus
    source_type: str
    mime_type: str | None = None


class SearchDocumentMatch(BaseModel):
    document_id: str
    chunk_id: str
    document_title: str
    chunk_index: int
    snippet: str


class SearchDocumentsToolOutput(BaseModel):
    matches: list[SearchDocumentMatch]


class GetDocumentToolOutput(BaseModel):
    document: ToolDocumentSummary


class ListWorkspaceDocumentsToolOutput(BaseModel):
    documents: list[ToolDocumentSummary]
