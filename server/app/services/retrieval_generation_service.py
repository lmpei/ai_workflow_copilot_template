from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urlparse

from app.core.config import get_settings
from app.schemas.chat import SourceReference
from app.services.indexing_service import DocumentIndexingError, get_embedding_provider
from app.services.model_interface_service import (
    ModelInterfaceError,
    ModelMessage,
    OpenAICompatibleModelInterface,
    OpenAICompatibleModelSettings,
    resolve_api_key,
)

RETRIEVAL_LIMIT = 4
FALLBACK_ANSWER = "I couldn't find relevant indexed content in this workspace."
SNIPPET_LENGTH = 240


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
                    snippet=build_snippet(str(content)),
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

        prompt = build_grounded_prompt(question=question, retrieved_chunks=retrieved_chunks)
        try:
            response = OpenAICompatibleModelInterface(
                settings=OpenAICompatibleModelSettings(
                    api_key=self.api_key,
                    model=self.model,
                    base_url=self.base_url,
                    provider_name=self.provider_name,
                )
            ).generate_text(
                temperature=0.2,
                messages=[
                    ModelMessage(
                        role="system",
                        content=(
                            "You answer using only the provided workspace context. "
                            "If the context is insufficient, say so plainly."
                        ),
                    ),
                    ModelMessage(role="user", content=prompt),
                ],
            )
        except ModelInterfaceError as error:
            raise ChatProcessingError("Failed to generate a grounded answer") from error

        answer = response.text
        if not answer.strip():
            raise ChatProcessingError("LLM returned an empty grounded answer")

        return GeneratedAnswer(
            answer=answer,
            prompt=prompt,
            token_input=response.usage.input_tokens,
            token_output=response.usage.output_tokens,
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

    api_key = resolve_api_key(
        provider_name=settings.chat_provider,
        configured_api_key=settings.chat_api_key,
        openai_api_key=settings.openai_api_key,
    )

    return OpenAICompatibleAnswerGenerator(
        api_key=api_key,
        model=settings.chat_model,
        base_url=settings.chat_base_url,
        provider_name=settings.chat_provider,
    )


def build_snippet(content: str) -> str:
    collapsed = " ".join(content.split())
    if len(collapsed) <= SNIPPET_LENGTH:
        return collapsed
    return f"{collapsed[: SNIPPET_LENGTH - 3].rstrip()}..."


def build_grounded_prompt(*, question: str, retrieved_chunks: list[RetrievedChunk]) -> str:
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

def serialize_sources(chunks: list[RetrievedChunk]) -> list[SourceReference]:
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
