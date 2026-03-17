from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.agents.tool_registry import (
    ToolExecutionError,
    UnknownToolError,
    get_tool_definition,
    invoke_tool,
    list_tool_definitions,
)
from app.repositories import document_repository, task_repository
from app.services.retrieval_service import RetrievedChunk


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


def _create_task_and_agent_run(*, workspace_id: str, user_id: str) -> tuple[str, str]:
    task = task_repository.create_task(
        workspace_id=workspace_id,
        task_type="research_summary",
        created_by=user_id,
        input_json={"goal": "Summarize documents"},
    )
    agent_run = task_repository.create_agent_run(
        task_id=task.id,
        agent_name="workspace_research_agent",
    )
    return task.id, agent_run.id


def test_tool_registry_resolves_stable_tool_names() -> None:
    definitions = list_tool_definitions()
    assert [definition.name for definition in definitions] == [
        "search_documents",
        "get_document",
        "list_workspace_documents",
    ]
    assert get_tool_definition("search_documents").name == "search_documents"


def test_invoke_search_documents_persists_completed_tool_call(
    client: TestClient,
    monkeypatch,
) -> None:
    class FakeRetriever:
        def retrieve(self, *, workspace_id: str, question: str) -> list[RetrievedChunk]:
            assert workspace_id
            assert question == "Who owns the project?"
            return [
                RetrievedChunk(
                    document_id="doc-1",
                    chunk_id="chunk-1",
                    document_title="demo.txt",
                    chunk_index=0,
                    snippet="The owner is Alice.",
                    content="The owner is Alice.",
                ),
            ]

    monkeypatch.setattr("app.agents.tool_registry.get_retriever", lambda: FakeRetriever())

    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    workspace_id = _create_workspace(client, auth["token"])
    _, agent_run_id = _create_task_and_agent_run(workspace_id=workspace_id, user_id=auth["user_id"])

    result = invoke_tool(
        agent_run_id=agent_run_id,
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        tool_name="search_documents",
        tool_input={"query": "Who owns the project?", "limit": 1},
    )

    assert result.output == {
        "matches": [
            {
                "document_id": "doc-1",
                "chunk_id": "chunk-1",
                "document_title": "demo.txt",
                "chunk_index": 0,
                "snippet": "The owner is Alice.",
            },
        ],
    }

    tool_call = task_repository.get_tool_call(result.tool_call_id)
    assert tool_call is not None
    assert tool_call.status == "completed"
    assert tool_call.tool_input_json == {"query": "Who owns the project?", "limit": 1}
    assert tool_call.tool_output_json == result.output
    assert tool_call.latency_ms >= 0


def test_invoke_list_workspace_documents_returns_structured_payload(client: TestClient) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    workspace_id = _create_workspace(client, auth["token"])
    _, agent_run_id = _create_task_and_agent_run(workspace_id=workspace_id, user_id=auth["user_id"])

    document_repository.create_document(
        document_id=str(uuid4()),
        workspace_id=workspace_id,
        title="demo.txt",
        file_path="uploads/demo.txt",
        mime_type="text/plain",
        created_by=auth["user_id"],
    )

    result = invoke_tool(
        agent_run_id=agent_run_id,
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        tool_name="list_workspace_documents",
        tool_input={"limit": 10},
    )

    assert len(result.output["documents"]) == 1
    assert result.output["documents"][0]["title"] == "demo.txt"
    assert result.output["documents"][0]["status"] == "uploaded"


def test_unknown_tool_name_is_persisted_as_failed(client: TestClient) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    workspace_id = _create_workspace(client, auth["token"])
    _, agent_run_id = _create_task_and_agent_run(workspace_id=workspace_id, user_id=auth["user_id"])

    with pytest.raises(UnknownToolError) as error:
        invoke_tool(
            agent_run_id=agent_run_id,
            workspace_id=workspace_id,
            user_id=auth["user_id"],
            tool_name="unknown_tool",
            tool_input={},
        )

    tool_call = task_repository.get_tool_call(error.value.tool_call_id)
    assert tool_call is not None
    assert tool_call.status == "failed"
    assert tool_call.tool_output_json == {"error": "Unknown tool: unknown_tool"}


def test_tool_failure_is_persisted_as_failed(
    client: TestClient,
    monkeypatch,
) -> None:
    class FailingRetriever:
        def retrieve(self, *, workspace_id: str, question: str) -> list[RetrievedChunk]:
            raise RuntimeError("Chroma unavailable")

    monkeypatch.setattr("app.agents.tool_registry.get_retriever", lambda: FailingRetriever())

    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    workspace_id = _create_workspace(client, auth["token"])
    _, agent_run_id = _create_task_and_agent_run(workspace_id=workspace_id, user_id=auth["user_id"])

    with pytest.raises(ToolExecutionError) as error:
        invoke_tool(
            agent_run_id=agent_run_id,
            workspace_id=workspace_id,
            user_id=auth["user_id"],
            tool_name="search_documents",
            tool_input={"query": "Who owns the project?"},
        )

    tool_call = task_repository.get_tool_call(error.value.tool_call_id)
    assert tool_call is not None
    assert tool_call.status == "failed"
    assert tool_call.tool_output_json == {"error": "Chroma unavailable"}

