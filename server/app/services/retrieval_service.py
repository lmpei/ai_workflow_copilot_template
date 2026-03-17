from datetime import UTC, datetime

from app.repositories import conversation_repository, workspace_repository
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.retrieval_generation_service import (
    FALLBACK_ANSWER,
    AnswerGenerator,
    ChatProcessingError,
    GeneratedAnswer,
    RetrievedChunk,
    Retriever,
    get_answer_generator,
    get_retriever,
    serialize_sources,
)
from app.services.trace_service import record_chat_trace


class ChatAccessError(Exception):
    pass


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

    conversation_repository.create_message(
        conversation_id=conversation.id,
        role="user",
        content=payload.question,
        metadata_json={"mode": payload.mode},
    )

    started_at = datetime.now(UTC)
    retrieved_chunks: list[RetrievedChunk] = []
    sources = []
    prompt = ""
    answer = ""
    token_input = 0
    token_output = 0
    estimated_cost = 0.0

    try:
        retriever: Retriever = get_retriever()
        answer_generator: AnswerGenerator = get_answer_generator()
        retrieved_chunks = retriever.retrieve(workspace_id=workspace_id, question=payload.question)
        sources = serialize_sources(retrieved_chunks)

        if retrieved_chunks:
            generated: GeneratedAnswer = answer_generator.generate_answer(
                question=payload.question,
                retrieved_chunks=retrieved_chunks,
            )
            answer = generated.answer
            prompt = generated.prompt
            token_input = generated.token_input
            token_output = generated.token_output
            estimated_cost = generated.estimated_cost
        else:
            answer = FALLBACK_ANSWER

        serialized_sources = [source.model_dump() for source in sources]
        conversation_repository.create_message(
            conversation_id=conversation.id,
            role="assistant",
            content=answer,
            metadata_json={"mode": payload.mode, "sources": serialized_sources},
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
            sources=serialized_sources,
            retrieved_chunks=serialized_sources,
            prompt=prompt,
            latency_ms=latency_ms,
            token_input=token_input,
            token_output=token_output,
            estimated_cost=estimated_cost,
        )
        return ChatResponse(answer=answer, sources=sources, trace_id=trace_id)
    except ChatProcessingError as error:
        conversation_repository.touch_conversation(conversation.id)
        latency_ms = max(
            int((datetime.now(UTC) - started_at).total_seconds() * 1000),
            0,
        )
        record_chat_trace(
            workspace_id=workspace_id,
            conversation_id=conversation.id,
            question=payload.question,
            answer=answer,
            mode=payload.mode,
            sources=[source.model_dump() for source in sources],
            retrieved_chunks=[source.model_dump() for source in sources],
            prompt=prompt,
            latency_ms=latency_ms,
            token_input=token_input,
            token_output=token_output,
            estimated_cost=estimated_cost,
            error=str(error),
        )
        raise
    except Exception as error:
        conversation_repository.touch_conversation(conversation.id)
        latency_ms = max(
            int((datetime.now(UTC) - started_at).total_seconds() * 1000),
            0,
        )
        record_chat_trace(
            workspace_id=workspace_id,
            conversation_id=conversation.id,
            question=payload.question,
            answer=answer,
            mode=payload.mode,
            sources=[source.model_dump() for source in sources],
            retrieved_chunks=[source.model_dump() for source in sources],
            prompt=prompt,
            latency_ms=latency_ms,
            token_input=token_input,
            token_output=token_output,
            estimated_cost=estimated_cost,
            error=str(error),
        )
        raise ChatProcessingError("Failed to process chat request") from error
