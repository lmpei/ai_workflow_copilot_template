from datetime import UTC, datetime

from app.repositories import conversation_repository, workspace_repository
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.trace_service import record_chat_trace


class ChatAccessError(Exception):
    pass


def retrieve_context(workspace_id: str, question: str) -> list[str]:
    return [
        f"Workspace: {workspace_id}",
        f"Relevant context for question: {question}",
    ]


def generate_answer(question: str, context: list[str]) -> str:
    return f"Stub answer for '{question}'. Context items: {len(context)}"


def _build_conversation_title(question: str) -> str:
    title = question.strip() or "New conversation"
    return title[:255]


def process_chat_request(
    *,
    workspace_id: str,
    user_id: str,
    payload: ChatRequest,
) -> ChatResponse:
    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        raise ChatAccessError("Workspace not found")

    if payload.conversation_id is None:
        conversation = conversation_repository.create_conversation(
            workspace_id=workspace_id,
            user_id=user_id,
            title=_build_conversation_title(payload.question),
        )
    else:
        existing_conversation = conversation_repository.get_conversation(
            conversation_id=payload.conversation_id,
            workspace_id=workspace_id,
            user_id=user_id,
        )
        if existing_conversation is None:
            raise ChatAccessError("Conversation not found")
        conversation = existing_conversation

    started_at = datetime.now(UTC)
    context = retrieve_context(workspace_id=workspace_id, question=payload.question)
    answer = generate_answer(question=payload.question, context=context)
    sources: list[dict[str, str]] = []

    conversation_repository.create_message(
        conversation_id=conversation.id,
        role="user",
        content=payload.question,
        metadata_json={"mode": payload.mode},
    )
    conversation_repository.create_message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
        metadata_json={"mode": payload.mode, "sources": sources},
    )
    conversation_repository.touch_conversation(conversation.id)

    latency_ms = max(
        int((datetime.now(UTC) - started_at).total_seconds() * 1000),
        0,
    )
    trace_id = record_chat_trace(
        workspace_id=workspace_id,
        conversation_id=conversation.id,
        question=payload.question,
        answer=answer,
        mode=payload.mode,
        sources=sources,
        latency_ms=latency_ms,
    )
    return ChatResponse(
        answer=answer,
        sources=[],
        trace_id=trace_id,
    )
