from typing import Literal

from pydantic import BaseModel

from app.schemas.research_external_resource_snapshot import (
    ResearchExternalResourceSnapshotResponse,
)

ChatSourceKind = Literal["workspace_document", "external_context"]
ChatMode = Literal["rag", "research_tool_assisted", "research_external_context"]


class ChatRequest(BaseModel):
    question: str
    conversation_id: str | None = None
    mode: ChatMode = "rag"
    external_resource_snapshot_id: str | None = None


class ChatToolStep(BaseModel):
    tool_name: str
    summary: str
    detail: str | None = None


class SourceReference(BaseModel):
    document_id: str
    chunk_id: str
    document_title: str
    chunk_index: int
    snippet: str
    source_kind: ChatSourceKind = "workspace_document"


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceReference]
    trace_id: str
    mode: ChatMode = "rag"
    tool_steps: list[ChatToolStep] = []
    external_resource_snapshot: ResearchExternalResourceSnapshotResponse | None = None
