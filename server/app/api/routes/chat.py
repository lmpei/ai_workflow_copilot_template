from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse, SourceReference
from app.services.retrieval_service import generate_answer, retrieve_context

router = APIRouter()


@router.post("/workspaces/{workspace_id}/chat", response_model=ChatResponse)
async def chat(workspace_id: str, payload: ChatRequest) -> ChatResponse:
    context = retrieve_context(workspace_id=workspace_id, question=payload.question)
    answer = generate_answer(question=payload.question, context=context)
    return ChatResponse(
        answer=answer,
        sources=[SourceReference(document_id="demo-doc", chunk_id="demo-chunk")],
        trace_id=f"trace-{workspace_id}",
    )
