from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from urllib.parse import urlparse

import httpx

from app.core.config import get_settings
from app.repositories import conversation_repository, workspace_repository
from app.schemas.chat import ChatRequest, ChatResponse, SourceReference
from app.services.indexing_service import DocumentIndexingError, get_embedding_provider
from app.services.trace_service import record_chat_trace

RETRIEVAL_LIMIT = 4
FALLBACK_ANSWER = "I couldn't find relevant indexed content in this workspace."
SNIPPET_LENGTH = 240


class ChatAccessError(Exception):
    pass


class ChatProcessingError(Exception):
    pass


@dataclass(slots=True)
class RetrievedChunk:
    document_id: str
    chunk_id: str
    document_title: str
    chunk_index: int
    snippet: str
    content: str


@dataclass(slots=True)
class GeneratedAnswer:
    answer: str
    prompt: str
    token_input: int = 0
    token_output: int = 0
    estimated_cost: float = 0.0


class Retriever(Protocol):
    def retrieve(self, *, workspace_id: str, question: str) -> list[RetrievedChunk]: ...


class AnswerGenerator(Protocol):
    def generate_answer(
        self,
        *,
        question: str,
        retrieved_chunks: list[RetrievedChunk],
    ) -> GeneratedAnswer: ...


@dataclass(slots=True)
class ChromaRetriever:
    url: str
    collection_name: str
    max_results: int = RETRIEVAL_LIMIT

    def _get_collection(self) -> Any:
        try:
            import chromadb
        except ImportError as error:
            raise ChatProcessingError("Chroma dependency is not installed") from error

        parsed = urlparse(self.url)
        host = parsed.hostname or "localhost"
        if parsed.scheme == "https":
            port = parsed.port or 443
        else:
            port = parsed.port or 8000

        try:
            client = chromadb.HttpClient(host=host, port=port, ssl=parsed.scheme == "https")
            return client.get_or_create_collection(name=self.collection_name)
        except Exception as error:
            raise ChatProcessingError("Failed to connect to Chroma collection") from error

    def retrieve(self, *, workspace_id: str, question: str) -> list[RetrievedChunk]:
        try:
            query_embedding = get_embedding_provider().embed_texts([question])[0]
        except (DocumentIndexingError, IndexError) as error:
            raise ChatProcessingError(str(error)) from error

        collection = self._get_collection()
        try:
            result = collection.query(
                query_embeddings=[query_embedding],
                n_results=self.max_results,
                where={"workspace_id": workspace_id},
                include=["documents", "metadatas"],
            )
        except Exception as error:
            raise ChatProcessingError("Failed to retrieve indexed chunks") from error

        ids = result.get("ids", [[]])
        documents = result.get("documents", [[]])
        metadatas = result.get("metadatas", [[]])
        if not ids or not ids[0]:
            return []

        retrieved_chunks: list[RetrievedChunk] = []
        for chunk_id, content, metadata in zip(ids[0], documents[0], metadatas[0], strict=False):
            if not isinstance(metadata, dict):
                continue
            retrieved_chunks.append(
                RetrievedChunk(
                    document_id=str(metadata.get("document_id", "")),
                    chunk_id=str(metadata.get("chunk_id", chunk_id)),
                    document_title=str(metadata.get("document_title", "")),
                    chunk_index=int(metadata.get("chunk_index", 0)),
                    snippet=_build_snippet(str(content)),
                    content=str(content),
                ),
            )
        return retrieved_chunks


@dataclass(slots=True)
class OpenAICompatibleAnswerGenerator:
    api_key: str
    model: str
    base_url: str = "https://api.openai.com/v1"
    provider_name: str = "openai"

    def generate_answer(
        self,
        *,
        question: str,
        retrieved_chunks: list[RetrievedChunk],
    ) -> GeneratedAnswer:
        if not self.api_key or self.api_key == "replace_me":
            raise ChatProcessingError(
                f"{self.provider_name} chat API key must be configured for chat generation",
            )

        prompt = _build_grounded_prompt(question=question, retrieved_chunks=retrieved_chunks)
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "temperature": 0.2,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You answer using only the provided workspace context. "
                                "If the context is insufficient, say so plainly."
                            ),
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                },
                timeout=30.0,
            )
            response.raise_for_status()
            payload = response.json()
            answer = _extract_chat_completion_text(payload)
            usage = payload.get("usage", {})
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
            raise ChatProcessingError("Failed to generate a grounded answer") from error

        if not answer.strip():
            raise ChatProcessingError("LLM returned an empty grounded answer")

        return GeneratedAnswer(
            answer=answer,
            prompt=prompt,
            token_input=int(usage.get("prompt_tokens", 0)),
            token_output=int(usage.get("completion_tokens", 0)),
            estimated_cost=0.0,
        )


def get_retriever() -> Retriever:
    settings = get_settings()
    return ChromaRetriever(
        url=settings.chroma_url,
        collection_name=settings.chroma_collection_name,
    )


def get_answer_generator() -> AnswerGenerator:
    settings = get_settings()
    if settings.chat_provider not in {"openai", "qwen"}:
        raise ChatProcessingError(f"Unsupported chat provider: {settings.chat_provider}")
    api_key = settings.chat_api_key
    if api_key == "replace_me" and settings.chat_provider == "openai":
        api_key = settings.openai_api_key
    return OpenAICompatibleAnswerGenerator(
        api_key=api_key,
        model=settings.chat_model,
        base_url=settings.chat_base_url,
        provider_name=settings.chat_provider,
    )


def _build_snippet(content: str) -> str:
    collapsed = " ".join(content.split())
    if len(collapsed) <= SNIPPET_LENGTH:
        return collapsed
    return f"{collapsed[: SNIPPET_LENGTH - 1].rstrip()}…"


def _build_grounded_prompt(*, question: str, retrieved_chunks: list[RetrievedChunk]) -> str:
    context_blocks = [
        (
            f"[{chunk.document_title} | chunk {chunk.chunk_index} | {chunk.chunk_id}]\n"
            f"{chunk.content}"
        )
        for chunk in retrieved_chunks
    ]
    context_text = "\n\n".join(context_blocks)
    return (
        "Question:\n"
        f"{question}\n\n"
        "Workspace context:\n"
        f"{context_text}\n\n"
        "Answer the question using the context above. If the context is incomplete, say so."
    )


def _extract_chat_completion_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise KeyError("choices")

    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise KeyError("message")

    content = message.get("content")
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = [
            str(item.get("text", ""))
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        return "\n".join(part for part in text_parts if part)

    raise TypeError("Unsupported chat completion content type")


def _build_conversation_title(question: str) -> str:
    title = question.strip() or "New conversation"
    return title[:255]


def _serialize_sources(chunks: list[RetrievedChunk]) -> list[SourceReference]:
    return [
        SourceReference(
            document_id=chunk.document_id,
            chunk_id=chunk.chunk_id,
            document_title=chunk.document_title,
            chunk_index=chunk.chunk_index,
            snippet=chunk.snippet,
        )
        for chunk in chunks
    ]


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
    sources: list[SourceReference] = []
    prompt = ""
    answer = ""
    token_input = 0
    token_output = 0
    estimated_cost = 0.0

    try:
        retriever = get_retriever()
        answer_generator = get_answer_generator()
        retrieved_chunks = retriever.retrieve(workspace_id=workspace_id, question=payload.question)
        sources = _serialize_sources(retrieved_chunks)

        if retrieved_chunks:
            generated = answer_generator.generate_answer(
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
        return ChatResponse(
            answer=answer,
            sources=sources,
            trace_id=trace_id,
        )
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
