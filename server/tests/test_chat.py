from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy import select

from app.connectors.research_external_context_connector import ResearchExternalContextEntry
from app.core.database import session_scope
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.trace import Trace
from app.repositories.document_repository import (
    DocumentChunkCreate,
    create_document,
    replace_document_chunks,
)
from app.schemas.chat import ChatToolStep, SourceReference
from app.services import retrieval_service
from app.services.research_external_context_service import ResearchExternalContextChatResult
from app.services.research_external_resource_snapshot_service import (
    create_research_external_resource_snapshot,
)
from app.schemas.ai_frontier_research import AiHotTrackerReportResponse
from app.services.research_tool_assisted_chat_service import ToolAssistedResearchChatResult
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
        json={"name": name, "module_type": "research"},
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
            "source_kind": "workspace_document",
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
            "source_kind": "workspace_document",
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


def test_chat_supports_research_tool_assisted_mode(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    def fake_run_tool_assisted_research_chat(*, workspace_id: str, user_id: str, question: str) -> ToolAssistedResearchChatResult:
        assert workspace_id
        assert user_id
        assert question == "Please analyze the current research question"
        return ToolAssistedResearchChatResult(
            answer="This is the tool-assisted pilot conclusion.",
            prompt="tool assisted prompt",
            sources=[],
            tool_steps=[],
            token_input=17,
            token_output=9,
            analysis_focus="Current research question",
            search_query="current research question",
            degraded_reason="no_grounded_matches",
        )

    monkeypatch.setattr(retrieval_service, "run_tool_assisted_research_chat", fake_run_tool_assisted_research_chat)

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/chat",
        json={"question": "Please analyze the current research question", "mode": "research_tool_assisted"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "This is the tool-assisted pilot conclusion."
    assert data["mode"] == "research_tool_assisted"
    assert data["tool_steps"] == []

    with session_scope() as session:
        traces = list(session.scalars(select(Trace)))

    assert len(traces) == 1
    assert traces[0].trace_type == "research_tool_assisted"
    assert traces[0].response_json["tool_steps"] == []
    assert traces[0].response_json["degraded_reason"] == "no_grounded_matches"
    assert traces[0].metadata_json["analysis_focus"] == "Current research question"
    assert traces[0].metadata_json["search_query"] == "current research question"
    assert traces[0].metadata_json["degraded_reason"] == "no_grounded_matches"

def test_chat_supports_research_external_context_mode(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    def fake_run_research_external_context_chat(
        *,
        workspace_id: str,
        user_id: str,
        question: str,
        selected_external_resource_snapshot=None,
    ) -> ResearchExternalContextChatResult:
        assert workspace_id
        assert user_id
        assert question == "Please combine workspace material with external context"
        assert selected_external_resource_snapshot is None
        return ResearchExternalContextChatResult(
            answer="This pass blends workspace evidence with approved external context.",
            prompt="external context prompt",
            sources=[
                SourceReference(
                    document_id="doc-1",
                    chunk_id="chunk-1",
                    document_title="workspace-notes.txt",
                    chunk_index=0,
                    snippet="Workspace evidence snippet.",
                    source_kind="workspace_document",
                ),
                SourceReference(
                    document_id="external:market-cost-pressure",
                    chunk_id="external:market-cost-pressure",
                    document_title="Analyst note: margin pressure and price discipline",
                    chunk_index=0,
                    snippet="External analyst context.",
                    source_kind="external_context",
                ),
            ],
            tool_steps=[
                ChatToolStep(
                    tool_name="research_external_context",
                    summary="已命中已授权外部信息。",
                )
            ],
            token_input=21,
            token_output=10,
            analysis_focus="Blend internal and external evidence",
            search_query="pricing pressure",
            degraded_reason=None,
            connector_consent_state="granted",
            external_context_used=True,
            external_match_count=1,
            external_matches=[
                ResearchExternalContextEntry(
                    context_id="market-cost-pressure",
                    title="Analyst note: margin pressure and price discipline",
                    source_label="External market note",
                    keywords=("pricing", "pressure"),
                    snippet="External analyst context.",
                )
            ],
        )

    monkeypatch.setattr(
        retrieval_service,
        "run_research_external_context_chat",
        fake_run_research_external_context_chat,
    )

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/chat",
        json={"question": "Please combine workspace material with external context", "mode": "research_external_context"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "research_external_context"
    assert data["tool_steps"][0]["tool_name"] == "research_external_context"
    assert data["sources"][0]["source_kind"] == "workspace_document"
    assert data["sources"][1]["source_kind"] == "external_context"
    assert data["external_resource_snapshot"]["connector_id"] == "research_external_context"
    assert data["external_resource_snapshot"]["resource_count"] == 1
    assert data["external_resource_snapshot"]["resources"][0]["resource_id"] == "market-cost-pressure"

    with session_scope() as session:
        traces = list(session.scalars(select(Trace)))

    assert len(traces) == 1
    assert traces[0].trace_type == "research_external_context"
    assert traces[0].metadata_json["connector_id"] == "research_external_context"
    assert traces[0].metadata_json["external_context_used"] is True
    assert traces[0].metadata_json["external_resource_snapshot_id"] == data["external_resource_snapshot"]["id"]


def test_chat_supports_selecting_existing_external_resource_snapshot(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    captured_snapshot_ids: list[str | None] = []

    def fake_run_research_external_context_chat(
        *,
        workspace_id: str,
        user_id: str,
        question: str,
        selected_external_resource_snapshot=None,
    ) -> ResearchExternalContextChatResult:
        assert selected_external_resource_snapshot is not None
        return ResearchExternalContextChatResult(
            answer="Used the selected external snapshot.",
            prompt="selected snapshot prompt",
            sources=[
                SourceReference(
                    document_id="external:selected",
                    chunk_id="external:selected",
                    document_title="Selected snapshot evidence",
                    chunk_index=0,
                    snippet="Selected snapshot evidence.",
                    source_kind="external_context",
                )
            ],
            tool_steps=[
                ChatToolStep(
                    tool_name="research_external_context",
                    summary="Used the selected external resource snapshot.",
                )
            ],
            token_input=12,
            token_output=8,
            analysis_focus="Reuse the selected snapshot",
            search_query="pricing pressure",
            degraded_reason=None,
            connector_consent_state="granted",
            external_context_used=True,
            external_match_count=1,
            external_matches=[],
            selected_external_resource_snapshot_id=selected_external_resource_snapshot.id,
        )

    snapshot = create_research_external_resource_snapshot(
        workspace_id=workspace_id,
        conversation_id=None,
        created_by=auth["user_id"],
        connector_id="research_external_context",
        search_query="pricing pressure",
        analysis_focus="Reuse the selected snapshot",
        matches=[
            ResearchExternalContextEntry(
                context_id="external-1",
                title="Analyst note",
                source_label="External market note",
                keywords=("pricing", "pressure"),
                snippet="External analysts also see sustained pricing pressure.",
            )
        ],
    )
    snapshot_id = snapshot.id

    original_get_snapshot = retrieval_service.get_workspace_research_external_resource_snapshot
    monkeypatch.setattr(
        retrieval_service,
        "get_workspace_research_external_resource_snapshot",
        lambda **kwargs: (
            captured_snapshot_ids.append(kwargs["snapshot_id"]),
            original_get_snapshot(**kwargs),
        )[1],
    )
    monkeypatch.setattr(
        retrieval_service,
        "run_research_external_context_chat",
        fake_run_research_external_context_chat,
    )

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/chat",
        json={
            "question": "Reuse the selected snapshot",
            "mode": "research_external_context",
            "external_resource_snapshot_id": snapshot_id,
        },
        headers=headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["external_resource_snapshot"]["id"] == snapshot_id
    assert captured_snapshot_ids == [snapshot_id]


def test_generate_ai_hot_tracker_report_endpoint(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    monkeypatch.setattr(
        "app.api.routes.research_analysis_runs.generate_ai_hot_tracker_report",
        lambda **kwargs: AiHotTrackerReportResponse.model_validate(
            {
                "title": "本轮 AI 热点",
                "question": "生成一份热点报告",
                "output": {
                    "frontier_summary": "本轮出现了几个值得关注的变化。",
                    "trend_judgment": "框架和 agent 生态都在加速。",
                    "themes": [{"label": "Agent", "summary": "Agent 继续升温。"}],
                    "events": [],
                    "project_cards": [],
                    "reference_sources": [],
                },
                "source_catalog": [],
                "source_items": [],
                "source_failures": [],
                "source_set": {"mode": "ai_hot_tracker_structured_report"},
                "generated_at": "2026-04-16T08:00:00Z",
                "degraded_reason": None,
            }
        ),
    )

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/ai-hot-tracker/report",
        headers=headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "本轮 AI 热点"
    assert payload["output"]["frontier_summary"] == "本轮出现了几个值得关注的变化。"
    assert payload["source_set"]["mode"] == "ai_hot_tracker_structured_report"


def test_save_ai_frontier_record_succeeds_without_follow_ups(
    client: TestClient,
) -> None:
    auth = _register_and_login(client, email="tracker@example.com", name="Tracker")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/ai-frontier-records",
        headers=headers,
        json={
            "title": "本轮热点记录",
            "question": "生成本轮热点报告",
            "output": {
                "frontier_summary": "本轮有几条值得继续跟进的 AI 变化。",
                "trend_judgment": "模型能力和基础设施发布继续升温。",
                "themes": [{"label": "模型发布", "summary": "近期模型与能力更新比较密集。"}],
                "events": [],
                "project_cards": [],
                "reference_sources": [],
            },
            "source_set": {"mode": "ai_hot_tracker_structured_report"},
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["title"] == "本轮热点记录"
    assert payload["follow_ups"] == []
    assert payload["source_set"]["mode"] == "ai_hot_tracker_structured_report"
    assert payload["source_set"]["follow_ups"] == []
