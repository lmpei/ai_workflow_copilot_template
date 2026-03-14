from uuid import uuid4

import pytest

from app.core.database import reset_database_for_tests
from app.models.document import DOCUMENT_STATUS_INDEXED
from app.repositories import document_repository, task_repository
from app.repositories.user_repository import create_user
from app.repositories.workspace_repository import create_workspace
from app.schemas.workspace import WorkspaceCreate
from app.services.agent_service import (
    AgentAccessError,
    AgentRuntimeError,
    run_workspace_research_agent,
)
from app.services.retrieval_service import RetrievedChunk


@pytest.fixture(autouse=True)
def reset_database() -> None:
    reset_database_for_tests()


def _create_runtime_fixture(*, with_document: bool = True) -> tuple[str, str, str]:
    unique_suffix = uuid4().hex
    user = create_user(
        email=f"phase3-agent-{unique_suffix}@example.com",
        password_hash="not-used-in-this-test",
        name="Phase 3 Agent",
    )
    workspace = create_workspace(
        WorkspaceCreate(name="Phase 3 Agent Workspace", type="research"),
        owner_id=user.id,
    )
    task = task_repository.create_task(
        workspace_id=workspace.id,
        task_type="research_summary",
        created_by=user.id,
        input_json={"goal": "Summarize workspace findings"},
    )
    if with_document:
        document_repository.create_document(
            document_id=str(uuid4()),
            workspace_id=workspace.id,
            title="demo.txt",
            file_path="uploads/demo.txt",
            mime_type="text/plain",
            created_by=user.id,
            status=DOCUMENT_STATUS_INDEXED,
        )
    return user.id, workspace.id, task.id


def test_workspace_research_agent_completes_tool_using_workflow(
    monkeypatch: pytest.MonkeyPatch,
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

    user_id, workspace_id, task_id = _create_runtime_fixture()

    result = run_workspace_research_agent(
        task_id=task_id,
        workspace_id=workspace_id,
        user_id=user_id,
        goal="Who owns the project?",
    )

    assert result.agent_name == "workspace_research_agent"
    assert result.final_output["goal"] == "Who owns the project?"
    assert result.final_output["document_count"] == 1
    assert result.final_output["matches"][0]["document_title"] == "demo.txt"

    agent_runs = task_repository.list_task_agent_runs(task_id)
    assert len(agent_runs) == 1
    assert agent_runs[0].status == "completed"
    assert agent_runs[0].final_output == result.final_output

    tool_calls = task_repository.list_agent_run_tool_calls(result.agent_run_id)
    assert [tool_call.tool_name for tool_call in tool_calls] == [
        "list_workspace_documents",
        "search_documents",
    ]
    assert all(tool_call.status == "completed" for tool_call in tool_calls)


def test_workspace_research_agent_completes_with_minimal_available_context() -> None:
    user_id, workspace_id, task_id = _create_runtime_fixture(with_document=False)

    result = run_workspace_research_agent(
        task_id=task_id,
        workspace_id=workspace_id,
        user_id=user_id,
        goal="Summarize this workspace",
    )

    assert result.final_output["document_count"] == 0
    assert result.final_output["matches"] == []
    assert result.final_output["summary"] == "No workspace documents are available for analysis."

    tool_calls = task_repository.list_agent_run_tool_calls(result.agent_run_id)
    assert [tool_call.tool_name for tool_call in tool_calls] == ["list_workspace_documents"]
    assert tool_calls[0].status == "completed"


def test_workspace_research_agent_marks_agent_run_failed_on_tool_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingRetriever:
        def retrieve(self, *, workspace_id: str, question: str) -> list[RetrievedChunk]:
            raise RuntimeError("Chroma unavailable")

    monkeypatch.setattr("app.agents.tool_registry.get_retriever", lambda: FailingRetriever())

    user_id, workspace_id, task_id = _create_runtime_fixture()

    with pytest.raises(AgentRuntimeError) as error:
        run_workspace_research_agent(
            task_id=task_id,
            workspace_id=workspace_id,
            user_id=user_id,
            goal="Who owns the project?",
        )

    assert error.value.agent_run_id is not None
    agent_run = task_repository.get_agent_run(error.value.agent_run_id)
    assert agent_run is not None
    assert agent_run.status == "failed"
    assert agent_run.final_output == {"error": "Chroma unavailable"}

    tool_calls = task_repository.list_agent_run_tool_calls(agent_run.id)
    assert [tool_call.tool_name for tool_call in tool_calls] == [
        "list_workspace_documents",
        "search_documents",
    ]
    assert tool_calls[0].status == "completed"
    assert tool_calls[1].status == "failed"


def test_workspace_research_agent_rejects_foreign_task_access() -> None:
    user_id, workspace_id, task_id = _create_runtime_fixture()

    with pytest.raises(AgentAccessError, match="Task not found"):
        run_workspace_research_agent(
            task_id=task_id,
            workspace_id=workspace_id,
            user_id=str(uuid4()),
            goal="Who owns the project?",
        )
