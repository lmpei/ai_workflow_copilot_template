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
    run_workspace_job_agent,
    run_workspace_research_agent,
    run_workspace_support_agent,
)
from app.services.retrieval_service import RetrievedChunk


@pytest.fixture(autouse=True)
def reset_database() -> None:
    reset_database_for_tests()



def _create_runtime_fixture(
    *,
    with_document: bool = True,
    workspace_type: str = "research",
    task_type: str = "research_summary",
    input_json: dict[str, object] | None = None,
) -> tuple[str, str, str]:
    unique_suffix = uuid4().hex
    user = create_user(
        email=f"phase3-agent-{unique_suffix}@example.com",
        password_hash="not-used-in-this-test",
        name="Phase 3 Agent",
    )
    workspace = create_workspace(
        WorkspaceCreate(name="Phase 3 Agent Workspace", type=workspace_type),
        owner_id=user.id,
    )
    task = task_repository.create_task(
        workspace_id=workspace.id,
        task_type=task_type,
        created_by=user.id,
        input_json=input_json or {"goal": "Summarize workspace findings"},
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
    assert result.final_output["module_type"] == "research"
    assert result.final_output["task_type"] == "research_summary"
    assert result.final_output["title"] == "Research Summary"
    assert result.final_output["summary"].startswith("Reviewed 1 workspace document")
    assert result.final_output["highlights"] == ["demo.txt: The owner is Alice."]
    assert result.final_output["artifacts"]["document_count"] == 1
    assert result.final_output["artifacts"]["match_count"] == 1
    assert result.final_output["artifacts"]["matches"][0]["document_title"] == "demo.txt"
    assert result.final_output["evidence"][0]["metadata"]["document_id"] == "doc-1"
    assert result.final_output["metadata"]["goal"] == "Who owns the project?"

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

    assert result.final_output["module_type"] == "research"
    assert result.final_output["artifacts"]["document_count"] == 0
    assert result.final_output["artifacts"]["match_count"] == 0
    assert result.final_output["artifacts"]["matches"] == []
    assert result.final_output["evidence"] == []
    assert result.final_output["summary"] == "No workspace documents are available for analysis."

    tool_calls = task_repository.list_agent_run_tool_calls(result.agent_run_id)
    assert [tool_call.tool_name for tool_call in tool_calls] == ["list_workspace_documents"]
    assert tool_calls[0].status == "completed"



def test_workspace_support_agent_completes_grounded_reply_draft(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeRetriever:
        def retrieve(self, *, workspace_id: str, question: str) -> list[RetrievedChunk]:
            assert workspace_id
            assert question == "Customer cannot reset their password"
            return [
                RetrievedChunk(
                    document_id="doc-1",
                    chunk_id="chunk-1",
                    document_title="support-guide.md",
                    chunk_index=0,
                    snippet=(
                        "Reset links expire after 15 minutes; "
                        "users should request a new email."
                    ),
                    content=(
                        "Reset links expire after 15 minutes; "
                        "users should request a new email."
                    ),
                ),
            ]

    monkeypatch.setattr("app.agents.tool_registry.get_retriever", lambda: FakeRetriever())

    user_id, workspace_id, task_id = _create_runtime_fixture(
        workspace_type="support",
        task_type="reply_draft",
        input_json={"customer_issue": "Customer cannot reset their password"},
    )

    result = run_workspace_support_agent(
        task_id=task_id,
        workspace_id=workspace_id,
        user_id=user_id,
        customer_issue="Customer cannot reset their password",
    )

    assert result.agent_name == "workspace_support_agent"
    assert result.final_output["module_type"] == "support"
    assert result.final_output["task_type"] == "reply_draft"
    assert result.final_output["title"] == "Grounded Reply Draft"
    assert result.final_output["artifacts"]["document_count"] == 1
    assert result.final_output["artifacts"]["match_count"] == 1
    assert result.final_output["artifacts"]["draft_reply"].startswith(
        "Thanks for reaching out",
    )
    assert result.final_output["evidence"][0]["metadata"]["document_id"] == "doc-1"
    assert (
        result.final_output["metadata"]["customer_issue"]
        == "Customer cannot reset their password"
    )

    tool_calls = task_repository.list_agent_run_tool_calls(result.agent_run_id)
    assert [tool_call.tool_name for tool_call in tool_calls] == [
        "list_workspace_documents",
        "search_documents",
    ]



def test_workspace_support_agent_returns_bounded_shape_without_documents() -> None:
    user_id, workspace_id, task_id = _create_runtime_fixture(
        with_document=False,
        workspace_type="support",
        task_type="ticket_summary",
        input_json={"customer_issue": "Customer billing question"},
    )

    result = run_workspace_support_agent(
        task_id=task_id,
        workspace_id=workspace_id,
        user_id=user_id,
        customer_issue="Customer billing question",
    )

    assert result.final_output["module_type"] == "support"
    assert result.final_output["artifacts"]["document_count"] == 0
    assert result.final_output["artifacts"]["match_count"] == 0
    assert result.final_output["artifacts"]["matches"] == []
    assert (
        result.final_output["summary"]
        == "No support knowledge documents are available for this workspace."
    )
    assert result.final_output["evidence"] == []


def test_workspace_job_agent_completes_resume_match_with_grounded_signal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeRetriever:
        def retrieve(self, *, workspace_id: str, question: str) -> list[RetrievedChunk]:
            assert workspace_id
            assert question == "Platform engineer"
            return [
                RetrievedChunk(
                    document_id="doc-1",
                    chunk_id="chunk-1",
                    document_title="candidate_resume.md",
                    chunk_index=0,
                    snippet=(
                        "Strong Python backend experience "
                        "with API design and reliability work."
                    ),
                    content=(
                        "Strong Python backend experience "
                        "with API design and reliability work."
                    ),
                ),
            ]

    monkeypatch.setattr("app.agents.tool_registry.get_retriever", lambda: FakeRetriever())

    user_id, workspace_id, task_id = _create_runtime_fixture(
        workspace_type="job",
        task_type="resume_match",
        input_json={"target_role": "Platform engineer"},
    )

    result = run_workspace_job_agent(
        task_id=task_id,
        workspace_id=workspace_id,
        user_id=user_id,
        target_role="Platform engineer",
    )

    assert result.agent_name == "workspace_job_agent"
    assert result.final_output["module_type"] == "job"
    assert result.final_output["task_type"] == "resume_match"
    assert result.final_output["artifacts"]["fit_signal"] == "grounded_match_found"
    assert result.final_output["artifacts"]["recommended_next_step"].startswith(
        "Review the top grounded match",
    )
    assert result.final_output["evidence"][0]["metadata"]["document_id"] == "doc-1"
    assert result.final_output["metadata"]["target_role"] == "Platform engineer"

    tool_calls = task_repository.list_agent_run_tool_calls(result.agent_run_id)
    assert [tool_call.tool_name for tool_call in tool_calls] == [
        "list_workspace_documents",
        "search_documents",
    ]


def test_workspace_job_agent_returns_bounded_shape_without_documents() -> None:
    user_id, workspace_id, task_id = _create_runtime_fixture(
        with_document=False,
        workspace_type="job",
        task_type="jd_summary",
        input_json={"target_role": "Platform engineer"},
    )

    result = run_workspace_job_agent(
        task_id=task_id,
        workspace_id=workspace_id,
        user_id=user_id,
        target_role="Platform engineer",
    )

    assert result.final_output["module_type"] == "job"
    assert result.final_output["artifacts"]["document_count"] == 0
    assert result.final_output["artifacts"]["match_count"] == 0
    assert result.final_output["artifacts"]["fit_signal"] == "no_documents_available"
    assert result.final_output["summary"] == "No job documents are available for this workspace."
    assert result.final_output["evidence"] == []



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



def test_workspace_research_agent_rejects_invalid_module_task_combination() -> None:
    user_id, workspace_id, task_id = _create_runtime_fixture(workspace_type="support")

    with pytest.raises(AgentRuntimeError, match="Task type research_summary is not supported"):
        run_workspace_research_agent(
            task_id=task_id,
            workspace_id=workspace_id,
            user_id=user_id,
            goal="Who owns the project?",
        )



def test_workspace_support_agent_rejects_invalid_module_task_combination() -> None:
    user_id, workspace_id, task_id = _create_runtime_fixture(
        workspace_type="research",
        task_type="ticket_summary",
        input_json={"customer_issue": "Customer billing question"},
    )

    with pytest.raises(AgentRuntimeError, match="Task type ticket_summary is not supported"):
        run_workspace_support_agent(
            task_id=task_id,
            workspace_id=workspace_id,
            user_id=user_id,
            customer_issue="Customer billing question",
        )


def test_workspace_job_agent_rejects_invalid_module_task_combination() -> None:
    user_id, workspace_id, task_id = _create_runtime_fixture(
        workspace_type="research",
        task_type="jd_summary",
        input_json={"target_role": "Platform engineer"},
    )

    with pytest.raises(AgentRuntimeError, match="Task type jd_summary is not supported"):
        run_workspace_job_agent(
            task_id=task_id,
            workspace_id=workspace_id,
            user_id=user_id,
            target_role="Platform engineer",
        )
