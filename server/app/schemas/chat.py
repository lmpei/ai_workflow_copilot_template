from typing import Literal

from pydantic import BaseModel

ChatMode = Literal["rag", "research_tool_assisted"]


class ChatRequest(BaseModel):
    question: str
    conversation_id: str | None = None
    mode: ChatMode = "rag"


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


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceReference]
    trace_id: str
    mode: ChatMode = "rag"
    tool_steps: list[ChatToolStep] = []
