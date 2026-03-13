from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy import select

from app.core.database import session_scope
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.trace import Trace
from app.repositories.document_repository import (
    DocumentChunkCreate,
    create_document,
    replace_document_chunks,
)
from app.services import retrieval_service
from app.services.retrieval_service import (
    ChatProcessingError,
    GeneratedAnswer,
    RetrievedChunk,
)


class FakeRetriever:
    def __init__(
        self,
        *,
        chunks: list[RetrievedChunk] | None = None,
        error: str | None = None,
    ) -> None:
        self.chunks = chunks or []
        self.error = error
        self.calls: list[dict[str, str]] = []

    def retrieve(self, *, workspace_id: str, question: str) -> list[RetrievedChunk]:
        self.calls.append({"workspace_id": workspace_id, "question": question})
        if self.error:
            raise ChatProcessingError(self.error)
        return list(self.chunks)


class FakeAnswerGenerator:
    def __init__(
        self,
        *,
        answer: str = "Grounded answer from indexed content.",
        prompt: str = "grounded prompt",
        error: str | None = None,
    ) -> None:
        self.answer = answer
        self.prompt = prompt
        self.error = error
        self.calls: list[dict[str, object]] = []

    def generate_answer(
        self,
        *,
        question: str,
        retrieved_chunks: list[RetrievedChunk],
    ) -> GeneratedAnswer:
        self.calls.append({"question": question, "retrieved_chunks": list(retrieved_chunks)})
        if self.error:
            raise ChatProcessingError(self.error)
        return GeneratedAnswer(
            answer=self.answer,
            prompt=self.prompt,
            token_input=11,
            token_output=7,
            estimated_cost=0.0,
        )


def _patch_chat_dependencies(
    monkeypatch: MonkeyPatch,
    *,
    retriever: FakeRetriever,
    answer_generator: FakeAnswerGenerator,
) -> None:
    monkeypatch.setattr(retrieval_service, "get_retriever", lambda: retriever)
    monkeypatch.setattr(retrieval_service, "get_answer_generator", lambda: answer_generator)


def _register_and_login(client: TestClient, *, email: str, name: str) -> dict[str, str]:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "super-secret",
            "name": name,
        },
    )
    assert register_response.status_code == 201
    user = register_response.json()

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "super-secret",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {
        "user_id": user["id"],
        "token": token,
    }


def _create_workspace(client: TestClient, token: str, *, name: str = "Research Demo") -> str:
    response = client.post(
        "/api/v1/workspaces",
        json={"name": name, "type": "research"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_indexed_document_fixture(*, workspace_id: str, user_id: str) -> RetrievedChunk:
    document_id = str(uuid4())
    relative_path = Path("uploads") / workspace_id / document_id / "knowledge.txt"
    full_path = Path("storage") / relative_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text("Indexed workspace context for grounded chat.", encoding="utf-8")

    document = create_document(
        document_id=document_id,
        workspace_id=workspace_id,
        title="knowledge.txt",
        file_path=relative_path.as_posix(),
        mime_type="text/plain",
        created_by=user_id,
    )
    with session_scope() as session:
        persisted_document = session.get(type(document), document.id)
        assert persisted_document is not None
        persisted_document.status = "parsing"
        session.add(persisted_document)

    chunks = replace_document_chunks(
        document.id,
        [
            DocumentChunkCreate(
                chunk_index=0,
                content="Indexed workspace context for grounded chat.",
                token_count=6,
                metadata_json={"char_start": 0, "char_end": 42},
            ),
        ],
    )
    with session_scope() as session:
        persisted_document = session.get(type(document), document.id)
        assert persisted_document is not None
        persisted_document.status = "indexed"
        session.add(persisted_document)

    return RetrievedChunk(
        document_id=document.id,
        chunk_id=chunks[0].id,
        document_title=document.title,
        chunk_index=chunks[0].chunk_index,
        snippet="Indexed workspace context for grounded chat.",
        content=chunks[0].content,
    )


def test_chat_returns_grounded_answer_sources_messages_and_trace(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])
    indexed_chunk = _create_indexed_document_fixture(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
    )
    retriever = FakeRetriever(chunks=[indexed_chunk])
    answer_generator = FakeAnswerGenerator()
    _patch_chat_dependencies(
        monkeypatch,
        retriever=retriever,
        answer_generator=answer_generator,
    )

    unauthorized_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/chat",
        json={"question": "What is this?", "mode": "rag"},
    )
    assert unauthorized_response.status_code == 401

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/chat",
        json={"question": "What is this?", "mode": "rag"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Grounded answer from indexed content."
    assert data["sources"] == [
        {
            "document_id": indexed_chunk.document_id,
            "chunk_id": indexed_chunk.chunk_id,
            "document_title": indexed_chunk.document_title,
            "chunk_index": indexed_chunk.chunk_index,
            "snippet": indexed_chunk.snippet,
        },
    ]
    assert retriever.calls == [{"workspace_id": workspace_id, "question": "What is this?"}]
    assert len(answer_generator.calls) == 1

    with session_scope() as session:
        conversations = list(session.scalars(select(Conversation)))
        messages = list(session.scalars(select(Message).order_by(Message.created_at.asc())))
        traces = list(session.scalars(select(Trace)))

    assert len(conversations) == 1
    assert conversations[0].workspace_id == workspace_id
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"
    assert messages[1].metadata_json["sources"][0]["chunk_id"] == indexed_chunk.chunk_id
    assert len(traces) == 1
    assert traces[0].id == data["trace_id"]
    assert traces[0].token_input == 11
    assert traces[0].token_output == 7
    assert traces[0].request_json["prompt"] == "grounded prompt"
    assert traces[0].response_json["sources"][0]["document_id"] == indexed_chunk.document_id


def test_chat_reuses_existing_conversation_and_returns_fallback_when_no_chunks(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])
    retriever = FakeRetriever(chunks=[])
    answer_generator = FakeAnswerGenerator()
    _patch_chat_dependencies(
        monkeypatch,
        retriever=retriever,
        answer_generator=answer_generator,
    )

    first_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/chat",
        json={"question": "First question", "mode": "rag"},
        headers=headers,
    )
    assert first_response.status_code == 200
    assert first_response.json()["answer"] == retrieval_service.FALLBACK_ANSWER
    assert first_response.json()["sources"] == []
    assert answer_generator.calls == []

    with session_scope() as session:
        conversation = session.scalar(select(Conversation))

    second_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/chat",
        json={
            "question": "Second question",
            "mode": "rag",
            "conversation_id": conversation.id,
        },
        headers=headers,
    )
    assert second_response.status_code == 200
    assert second_response.json()["answer"] == retrieval_service.FALLBACK_ANSWER

    with session_scope() as session:
        conversations = list(session.scalars(select(Conversation)))
        messages = list(session.scalars(select(Message).order_by(Message.created_at.asc())))
        traces = list(session.scalars(select(Trace).order_by(Trace.created_at.asc())))

    assert len(conversations) == 1
    assert [message.role for message in messages] == ["user", "assistant", "user", "assistant"]
    assert [trace.trace_type for trace in traces] == ["rag", "rag"]


def test_chat_records_error_trace_when_answer_generation_fails(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])
    indexed_chunk = _create_indexed_document_fixture(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
    )
    retriever = FakeRetriever(chunks=[indexed_chunk])
    answer_generator = FakeAnswerGenerator(error="LLM unavailable")
    _patch_chat_dependencies(
        monkeypatch,
        retriever=retriever,
        answer_generator=answer_generator,
    )

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/chat",
        json={"question": "What is this?", "mode": "rag"},
        headers=headers,
    )
    assert response.status_code == 500
    assert response.json()["detail"] == "LLM unavailable"

    with session_scope() as session:
        conversations = list(session.scalars(select(Conversation)))
        messages = list(session.scalars(select(Message).order_by(Message.created_at.asc())))
        traces = list(session.scalars(select(Trace)))

    assert len(conversations) == 1
    assert [message.role for message in messages] == ["user"]
    assert len(traces) == 1
    assert traces[0].response_json["error"] == "LLM unavailable"
    assert traces[0].response_json["sources"] == [
        {
            "document_id": indexed_chunk.document_id,
            "chunk_id": indexed_chunk.chunk_id,
            "document_title": indexed_chunk.document_title,
            "chunk_index": indexed_chunk.chunk_index,
            "snippet": indexed_chunk.snippet,
        },
    ]


def test_chat_rejects_foreign_conversation_id(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    first_workspace_id = _create_workspace(client, auth["token"], name="Workspace One")
    second_workspace_id = _create_workspace(client, auth["token"], name="Workspace Two")
    _patch_chat_dependencies(
        monkeypatch,
        retriever=FakeRetriever(chunks=[]),
        answer_generator=FakeAnswerGenerator(),
    )

    first_response = client.post(
        f"/api/v1/workspaces/{first_workspace_id}/chat",
        json={"question": "Owner question", "mode": "rag"},
        headers=headers,
    )
    assert first_response.status_code == 200

    with session_scope() as session:
        conversation = session.scalar(select(Conversation))

    response = client.post(
        f"/api/v1/workspaces/{second_workspace_id}/chat",
        json={
            "question": "Second workspace question",
            "mode": "rag",
            "conversation_id": conversation.id,
        },
        headers=headers,
    )
    assert response.status_code == 404
