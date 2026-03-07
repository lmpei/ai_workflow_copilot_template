from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    conversation_id: str | None = None
    mode: str = "rag"


class SourceReference(BaseModel):
    document_id: str
    chunk_id: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceReference]
    trace_id: str
