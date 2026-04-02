from uuid import uuid4

from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy import select

from app.core.database import session_scope
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.research_analysis_run import ResearchAnalysisRun
from app.models.trace import Trace
from app.schemas.chat import ChatToolStep, SourceReference
from app.services import research_analysis_run_service
from app.services.research_external_context_service import ResearchExternalContextChatResult
from app.services.research_tool_assisted_chat_service import (
    ResearchRunMemoryContext,
    ToolAssistedResearchChatResult,
)


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
    return {"user_id": user["id"], "token": token}


def _create_workspace(client: TestClient, token: str, *, module_type: str = "research", name: str = "Research Demo") -> str:
    response = client.post(
        "/api/v1/workspaces",
        json={"name": name, "module_type": module_type},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_create_research_analysis_run_creates_pending_run_and_user_message(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    async def fake_enqueue(run_id: str) -> str:
        assert isinstance(run_id, str)
        return "job-1"

    monkeypatch.setattr(research_analysis_run_service, "enqueue_research_analysis_run_execution", fake_enqueue)

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/research-analysis-runs",
        json={
            "question": "Analyze the strongest signal in the current material.",
            "mode": "research_tool_assisted",
        },
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["question"] == "Analyze the strongest signal in the current material."
    assert data["mode"] == "research_tool_assisted"
    assert data["resumed_from_run_id"] is None
    assert data["run_memory"] is None

    list_response = client.get(
        f"/api/v1/workspaces/{workspace_id}/research-analysis-runs",
        headers=headers,
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["id"] == data["id"]

    with session_scope() as session:
        runs = list(session.scalars(select(ResearchAnalysisRun)))
        conversations = list(session.scalars(select(Conversation)))
        messages = list(session.scalars(select(Message).order_by(Message.created_at.asc())))

    assert len(runs) == 1
    assert runs[0].status == "pending"
    assert len(conversations) == 1
    assert [message.role for message in messages] == ["user"]
    assert messages[0].metadata_json["research_analysis_run_id"] == data["id"]
    assert messages[0].metadata_json["delivery"] == "background_run"


def test_create_research_analysis_run_reuses_latest_terminal_run_memory(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    async def fake_enqueue(run_id: str) -> str:
        return "job-1"

    monkeypatch.setattr(research_analysis_run_service, "enqueue_research_analysis_run_execution", fake_enqueue)

    first_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/research-analysis-runs",
        json={
            "question": "First bounded analysis",
            "mode": "research_tool_assisted",
        },
        headers=headers,
    )
    assert first_response.status_code == 201
    first_run_id = first_response.json()["id"]
    conversation_id = first_response.json()["conversation_id"]

    running = research_analysis_run_service.research_analysis_run_repository.update_research_analysis_run(
        first_run_id,
        next_status="running",
    )
    assert running is not None
    persisted = research_analysis_run_service.research_analysis_run_repository.update_research_analysis_run(
        first_run_id,
        next_status="completed",
        run_memory_json={
            "memory_version": 1,
            "summary": "Pricing pressure is the strongest signal so far.",
            "evidence_state": "grounded_matches",
            "recommended_next_step": "Generate a formal research summary next.",
            "source_titles": ["market-notes.txt"],
        },
    )
    assert persisted is not None

    second_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/research-analysis-runs",
        json={
            "question": "Continue the same analysis",
            "conversation_id": conversation_id,
            "mode": "research_tool_assisted",
        },
        headers=headers,
    )
    assert second_response.status_code == 201
    second_run = second_response.json()
    assert second_run["resumed_from_run_id"] == first_run_id


def test_create_research_analysis_run_rejects_non_research_workspace(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"], module_type="support", name="Support Demo")

    async def fake_enqueue(run_id: str) -> str:
        return "job-1"

    monkeypatch.setattr(research_analysis_run_service, "enqueue_research_analysis_run_execution", fake_enqueue)

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/research-analysis-runs",
        json={
            "question": "Analyze the current issue.",
            "mode": "research_tool_assisted",
        },
        headers=headers,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Background analysis runs are only available in Research workspaces"


def test_run_research_analysis_run_execution_completes_and_records_trace(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    async def fake_enqueue(run_id: str) -> str:
        return "job-1"

    monkeypatch.setattr(research_analysis_run_service, "enqueue_research_analysis_run_execution", fake_enqueue)

    create_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/research-analysis-runs",
        json={
            "question": "Analyze the strongest signal in the current material.",
            "mode": "research_tool_assisted",
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    run_id = create_response.json()["id"]

    def fake_run_tool_assisted_research_chat(
        *,
        workspace_id: str,
        user_id: str,
        question: str,
        prior_memory: ResearchRunMemoryContext | None = None,
    ) -> ToolAssistedResearchChatResult:
        assert workspace_id
        assert user_id
        assert question == "Analyze the strongest signal in the current material."
        assert prior_memory is None
        return ToolAssistedResearchChatResult(
            answer="The strongest current signal is the pricing shift.",
            prompt="analysis prompt",
            sources=[
                SourceReference(
                    document_id="doc-1",
                    chunk_id=str(uuid4()),
                    document_title="market-notes.txt",
                    chunk_index=0,
                    snippet="The strongest current signal is the pricing shift.",
                )
            ],
            tool_steps=[],
            token_input=18,
            token_output=12,
            analysis_focus="Find the strongest market signal",
            search_query="pricing shift market signal",
            degraded_reason="no_grounded_matches",
        )

    monkeypatch.setattr(research_analysis_run_service, "run_tool_assisted_research_chat", fake_run_tool_assisted_research_chat)

    execution_result = research_analysis_run_service.run_research_analysis_run_execution(run_id)
    assert execution_result["run_id"] == run_id
    assert execution_result["status"] == "degraded"

    get_response = client.get(
        f"/api/v1/research-analysis-runs/{run_id}",
        headers=headers,
    )
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["status"] == "degraded"
    assert data["analysis_focus"] == "Find the strongest market signal"
    assert data["search_query"] == "pricing shift market signal"
    assert data["degraded_reason"] == "no_grounded_matches"
    assert data["trace_id"]
    assert data["run_memory"]["summary"] == "The strongest current signal is the pricing shift."
    assert data["run_memory"]["evidence_state"] == "no_grounded_matches"

    with session_scope() as session:
        messages = list(session.scalars(select(Message).order_by(Message.created_at.asc())))
        traces = list(session.scalars(select(Trace)))

    assert [message.role for message in messages] == ["user", "assistant"]
    assert messages[1].metadata_json["research_analysis_run_id"] == run_id
    assert messages[1].metadata_json["run_memory"]["summary"] == "The strongest current signal is the pricing shift."
    assert len(traces) == 1
    assert traces[0].trace_type == "research_tool_assisted_run"
    assert traces[0].response_json["run_status"] == "degraded"
    assert traces[0].response_json["research_analysis_run_id"] == run_id
    assert traces[0].response_json["run_memory"]["evidence_state"] == "no_grounded_matches"


def test_run_research_analysis_run_execution_uses_prior_memory_when_resuming(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    async def fake_enqueue(run_id: str) -> str:
        return "job-1"

    monkeypatch.setattr(research_analysis_run_service, "enqueue_research_analysis_run_execution", fake_enqueue)

    first_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/research-analysis-runs",
        json={
            "question": "First bounded analysis",
            "mode": "research_tool_assisted",
        },
        headers=headers,
    )
    assert first_response.status_code == 201
    first_run_id = first_response.json()["id"]
    conversation_id = first_response.json()["conversation_id"]

    running = research_analysis_run_service.research_analysis_run_repository.update_research_analysis_run(
        first_run_id,
        next_status="running",
    )
    assert running is not None
    persisted = research_analysis_run_service.research_analysis_run_repository.update_research_analysis_run(
        first_run_id,
        next_status="completed",
        run_memory_json={
            "memory_version": 1,
            "summary": "Pricing pressure is the strongest signal so far.",
            "evidence_state": "grounded_matches",
            "recommended_next_step": "Generate a formal research summary next.",
            "source_titles": ["market-notes.txt"],
        },
    )
    assert persisted is not None

    second_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/research-analysis-runs",
        json={
            "question": "Continue the same analysis",
            "conversation_id": conversation_id,
            "mode": "research_tool_assisted",
        },
        headers=headers,
    )
    assert second_response.status_code == 201
    second_run_id = second_response.json()["id"]
    assert second_response.json()["resumed_from_run_id"] == first_run_id

    captured_prior_memory: list[ResearchRunMemoryContext | None] = []

    def fake_run_tool_assisted_research_chat(
        *,
        workspace_id: str,
        user_id: str,
        question: str,
        prior_memory: ResearchRunMemoryContext | None = None,
    ) -> ToolAssistedResearchChatResult:
        captured_prior_memory.append(prior_memory)
        return ToolAssistedResearchChatResult(
            answer="The follow-up pass confirms pricing pressure.",
            prompt="follow-up prompt",
            sources=[],
            tool_steps=[],
            token_input=10,
            token_output=8,
            analysis_focus="Confirm the strongest market signal",
            search_query="pricing pressure confirmation",
            degraded_reason="no_grounded_matches",
        )

    monkeypatch.setattr(research_analysis_run_service, "run_tool_assisted_research_chat", fake_run_tool_assisted_research_chat)

    execution_result = research_analysis_run_service.run_research_analysis_run_execution(second_run_id)
    assert execution_result["status"] == "degraded"
    assert len(captured_prior_memory) == 1
    assert captured_prior_memory[0] is not None
    assert captured_prior_memory[0].source_run_id == first_run_id
    assert captured_prior_memory[0].summary == "Pricing pressure is the strongest signal so far."

    get_response = client.get(
        f"/api/v1/research-analysis-runs/{second_run_id}",
        headers=headers,
    )
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["resumed_from_run_id"] == first_run_id
    assert data["run_memory"]["summary"] == "The follow-up pass confirms pricing pressure."


def test_list_workspace_research_analysis_run_review_returns_regression_summary(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    async def fake_enqueue(run_id: str) -> str:
        return "job-1"

    monkeypatch.setattr(research_analysis_run_service, "enqueue_research_analysis_run_execution", fake_enqueue)

    create_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/research-analysis-runs",
        json={
            "question": "Analyze the strongest signal in the current material.",
            "mode": "research_tool_assisted",
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    run_id = create_response.json()["id"]

    def fake_run_tool_assisted_research_chat(
        *,
        workspace_id: str,
        user_id: str,
        question: str,
        prior_memory: ResearchRunMemoryContext | None = None,
    ) -> ToolAssistedResearchChatResult:
        return ToolAssistedResearchChatResult(
            answer="The strongest current signal is the pricing shift.",
            prompt="analysis prompt",
            sources=[
                SourceReference(
                    document_id="doc-1",
                    chunk_id=str(uuid4()),
                    document_title="market-notes.txt",
                    chunk_index=0,
                    snippet="The strongest current signal is the pricing shift.",
                )
            ],
            tool_steps=[
                ChatToolStep(
                    tool_name="list_workspace_documents",
                    summary="Checked the workspace material.",
                )
            ],
            token_input=18,
            token_output=12,
            analysis_focus="Find the strongest market signal",
            search_query="pricing shift market signal",
            degraded_reason=None,
        )

    monkeypatch.setattr(research_analysis_run_service, "run_tool_assisted_research_chat", fake_run_tool_assisted_research_chat)
    research_analysis_run_service.run_research_analysis_run_execution(run_id)

    review_response = client.get(
        f"/api/v1/workspaces/{workspace_id}/research-analysis-runs/review",
        headers=headers,
    )
    assert review_response.status_code == 200
    payload = review_response.json()
    assert payload["baseline_version"] == "stage_h_research_run_regression_v1"
    assert payload["reviewed_count"] == 1
    assert payload["passing_count"] == 1
    assert payload["failing_count"] == 0
    assert payload["items"][0]["run_id"] == run_id
    assert payload["items"][0]["passed"] is True
    assert payload["items"][0]["issues"] == []

def test_run_research_analysis_run_execution_supports_external_context_mode(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    async def fake_enqueue(run_id: str) -> str:
        return "job-1"

    monkeypatch.setattr(research_analysis_run_service, "enqueue_research_analysis_run_execution", fake_enqueue)

    create_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/research-analysis-runs",
        json={
            "question": "Combine the workspace signal with outside context.",
            "mode": "research_external_context",
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    run_id = create_response.json()["id"]

    def fake_run_research_external_context_chat(
        *,
        workspace_id: str,
        user_id: str,
        question: str,
        prior_memory: ResearchRunMemoryContext | None = None,
    ) -> ResearchExternalContextChatResult:
        assert prior_memory is None
        return ResearchExternalContextChatResult(
            answer="Workspace evidence aligns with the approved external market note.",
            prompt="external run prompt",
            sources=[
                SourceReference(
                    document_id="doc-1",
                    chunk_id=str(uuid4()),
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
                    summary="Found one approved external context match.",
                )
            ],
            token_input=22,
            token_output=11,
            analysis_focus="Compare workspace evidence with external market context",
            search_query="pricing pressure",
            degraded_reason=None,
            connector_consent_state="granted",
            external_context_used=True,
            external_match_count=1,
        )

    monkeypatch.setattr(
        research_analysis_run_service,
        "run_research_external_context_chat",
        fake_run_research_external_context_chat,
    )

    execution_result = research_analysis_run_service.run_research_analysis_run_execution(run_id)
    assert execution_result["status"] == "completed"

    get_response = client.get(
        f"/api/v1/research-analysis-runs/{run_id}",
        headers=headers,
    )
    assert get_response.status_code == 200
    payload = get_response.json()
    assert payload["mode"] == "research_external_context"
    assert payload["status"] == "completed"
    assert payload["sources"][0]["source_kind"] == "workspace_document"
    assert payload["sources"][1]["source_kind"] == "external_context"

    with session_scope() as session:
        traces = list(session.scalars(select(Trace)))

    assert len(traces) == 1
    assert traces[0].trace_type == "research_external_context_run"
    assert traces[0].response_json["connector_id"] == "research_external_context"
    assert traces[0].response_json["external_context_used"] is True
