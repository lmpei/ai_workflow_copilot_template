import asyncio
from uuid import uuid4

import pytest

from app.core.database import reset_database_for_tests
from app.models.document import DOCUMENT_STATUS_INDEXED
from app.repositories import document_repository, task_repository
from app.repositories.user_repository import create_user
from app.repositories.workspace_repository import create_workspace
from app.schemas.workspace import WorkspaceCreate
from app.services import task_execution_service
from app.services.retrieval_service import RetrievedChunk
from app.services.task_execution_service import TaskExecutionError
from app.workers.task_worker import run_platform_task


class FakeJob:
    def __init__(self, job_id: str) -> None:
        self.job_id = job_id


class FakePool:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.closed = False

    async def enqueue_job(self, function_name: str, task_id: str, _queue_name: str) -> FakeJob:
        self.calls.append(
            {
                "function_name": function_name,
                "task_id": task_id,
                "queue_name": _queue_name,
            },
        )
        return FakeJob("job-123")

    async def aclose(self) -> None:
        self.closed = True


@pytest.fixture(autouse=True)
def reset_database() -> None:
    reset_database_for_tests()



def _create_task_fixture(
    *,
    task_type: str = "research_summary",
    goal: str | None = None,
    with_document: bool = True,
    workspace_type: str = "research",
    input_json: dict[str, object] | None = None,
) -> str:
    unique_suffix = uuid4().hex
    user = create_user(
        email=f"phase3-worker-{unique_suffix}@example.com",
        password_hash="not-used-in-this-test",
        name="Phase 3 Worker",
    )
    workspace = create_workspace(
        WorkspaceCreate(name="Phase 3 Worker Workspace", module_type=workspace_type),
        owner_id=user.id,
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
    task = task_repository.create_task(
        workspace_id=workspace.id,
        task_type=task_type,
        created_by=user.id,
        input_json=(
            input_json
            if input_json is not None
            else ({"goal": goal} if goal is not None else {})
        ),
    )
    return task.id



def test_enqueue_task_execution_uses_arq_pool(monkeypatch: pytest.MonkeyPatch) -> None:
    task_id = _create_task_fixture()
    fake_pool = FakePool()

    async def fake_create_pool(_settings: object) -> FakePool:
        return fake_pool

    monkeypatch.setattr(task_execution_service, "create_pool", fake_create_pool)
    monkeypatch.setattr(task_execution_service, "build_redis_settings", lambda: object())

    job_id = asyncio.run(task_execution_service.enqueue_task_execution(task_id))

    assert job_id == "job-123"
    assert fake_pool.calls == [
        {
            "function_name": task_execution_service.TASK_EXECUTION_JOB_NAME,
            "task_id": task_id,
            "queue_name": "platform_tasks",
        },
    ]
    assert fake_pool.closed is True



def test_run_task_execution_executes_research_summary_and_persists_output(
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

    task_id = _create_task_fixture(goal="Who owns the project?")

    output = task_execution_service.run_task_execution(task_id)
    persisted_task = task_repository.get_task(task_id)

    assert output["worker"] == "arq"
    assert output["task_type"] == "research_summary"
    assert output["agent_name"] == "workspace_research_agent"
    assert output["result"]["module_type"] == "research"
    assert output["result"]["task_type"] == "research_summary"
    assert output["result"]["input"]["goal"] == "Who owns the project?"
    assert output["result"]["input"]["deliverable"] == "brief"
    assert output["result"]["sections"]["findings"][0]["evidence_ref_ids"] == ["chunk-1"]
    assert output["result"]["artifacts"]["matches"][0]["document_title"] == "demo.txt"
    assert output["result"]["evidence"][0]["metadata"]["document_id"] == "doc-1"
    assert persisted_task is not None
    assert persisted_task.status == "done"
    assert persisted_task.output_json == output

    agent_runs = task_repository.list_task_agent_runs(task_id)
    assert len(agent_runs) == 1
    assert agent_runs[0].status == "completed"

    tool_calls = task_repository.list_agent_run_tool_calls(agent_runs[0].id)
    assert [tool_call.tool_name for tool_call in tool_calls] == [
        "list_workspace_documents",
        "search_documents",
    ]
    assert all(tool_call.status == "completed" for tool_call in tool_calls)



def test_run_task_execution_completes_workspace_report_with_limited_context() -> None:
    task_id = _create_task_fixture(
        task_type="workspace_report",
        goal=None,
        with_document=False,
    )

    output = task_execution_service.run_task_execution(task_id)
    persisted_task = task_repository.get_task(task_id)

    assert output["task_type"] == "workspace_report"
    assert output["result"]["title"] == "Workspace Report"
    assert output["result"]["input"]["deliverable"] == "report"
    assert "open_questions" in output["result"]["sections"]
    assert output["result"]["artifacts"]["document_count"] == 0
    assert output["result"]["artifacts"]["matches"] == []
    assert output["result"]["summary"] == "No workspace documents are available for analysis."
    assert persisted_task is not None
    assert persisted_task.status == "done"

    agent_runs = task_repository.list_task_agent_runs(task_id)
    assert len(agent_runs) == 1
    tool_calls = task_repository.list_agent_run_tool_calls(agent_runs[0].id)
    assert [tool_call.tool_name for tool_call in tool_calls] == ["list_workspace_documents"]



def test_run_task_execution_executes_support_reply_draft_and_persists_output(
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

    task_id = _create_task_fixture(
        task_type="reply_draft",
        workspace_type="support",
        input_json={"customer_issue": "Customer cannot reset their password"},
    )

    output = task_execution_service.run_task_execution(task_id)
    persisted_task = task_repository.get_task(task_id)

    assert output["task_type"] == "reply_draft"
    assert output["agent_name"] == "workspace_support_agent"
    assert output["result"]["module_type"] == "support"
    assert output["result"]["task_type"] == "reply_draft"
    assert output["result"]["artifacts"]["draft_reply"].startswith(
        "Thanks for reaching out",
    )
    assert output["result"]["artifacts"]["match_count"] == 1
    assert persisted_task is not None
    assert persisted_task.status == "done"



def test_run_task_execution_completes_support_ticket_summary_with_limited_context() -> None:
    task_id = _create_task_fixture(
        task_type="ticket_summary",
        workspace_type="support",
        with_document=False,
        input_json={"customer_issue": "Customer billing question"},
    )

    output = task_execution_service.run_task_execution(task_id)
    persisted_task = task_repository.get_task(task_id)

    assert output["task_type"] == "ticket_summary"
    assert output["result"]["title"] == "Support Ticket Summary"
    assert output["result"]["artifacts"]["document_count"] == 0
    assert output["result"]["artifacts"]["matches"] == []
    assert (
        output["result"]["summary"]
        == "No support knowledge documents are available for this workspace."
    )
    assert persisted_task is not None
    assert persisted_task.status == "done"


def test_run_task_execution_executes_job_resume_match_and_persists_output(
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

    task_id = _create_task_fixture(
        task_type="resume_match",
        workspace_type="job",
        input_json={"target_role": "Platform engineer"},
    )

    output = task_execution_service.run_task_execution(task_id)
    persisted_task = task_repository.get_task(task_id)

    assert output["task_type"] == "resume_match"
    assert output["agent_name"] == "workspace_job_agent"
    assert output["result"]["module_type"] == "job"
    assert output["result"]["artifacts"]["fit_signal"] == "grounded_match_found"
    assert persisted_task is not None
    assert persisted_task.status == "done"


def test_run_task_execution_completes_job_jd_summary_with_limited_context() -> None:
    task_id = _create_task_fixture(
        task_type="jd_summary",
        workspace_type="job",
        with_document=False,
        input_json={"target_role": "Platform engineer"},
    )

    output = task_execution_service.run_task_execution(task_id)
    persisted_task = task_repository.get_task(task_id)

    assert output["task_type"] == "jd_summary"
    assert output["result"]["title"] == "Job Description Summary"
    assert output["result"]["artifacts"]["document_count"] == 0
    assert output["result"]["artifacts"]["fit_signal"] == "no_documents_available"
    assert output["result"]["summary"] == "No job documents are available for this workspace."
    assert persisted_task is not None
    assert persisted_task.status == "done"



def test_run_task_execution_marks_task_failed_when_agent_execution_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingRetriever:
        def retrieve(self, *, workspace_id: str, question: str) -> list[RetrievedChunk]:
            raise RuntimeError("Chroma unavailable")

    monkeypatch.setattr("app.agents.tool_registry.get_retriever", lambda: FailingRetriever())

    task_id = _create_task_fixture(goal="Who owns the project?")

    with pytest.raises(TaskExecutionError, match="Task execution failed"):
        task_execution_service.run_task_execution(task_id)

    persisted_task = task_repository.get_task(task_id)
    assert persisted_task is not None
    assert persisted_task.status == "failed"
    assert persisted_task.error_message == "Chroma unavailable"

    agent_runs = task_repository.list_task_agent_runs(task_id)
    assert len(agent_runs) == 1
    assert agent_runs[0].status == "failed"



def test_run_task_execution_rejects_invalid_module_task_combination() -> None:
    task_id = _create_task_fixture(goal="Who owns the project?", workspace_type="support")

    with pytest.raises(TaskExecutionError, match="Task type research_summary is not supported"):
        task_execution_service.run_task_execution(task_id)

    persisted_task = task_repository.get_task(task_id)
    assert persisted_task is not None
    assert persisted_task.status == "failed"



def test_run_task_execution_rejects_invalid_support_module_task_combination() -> None:
    task_id = _create_task_fixture(
        task_type="ticket_summary",
        workspace_type="research",
        input_json={"customer_issue": "Customer billing question"},
    )

    with pytest.raises(TaskExecutionError, match="Task type ticket_summary is not supported"):
        task_execution_service.run_task_execution(task_id)

    persisted_task = task_repository.get_task(task_id)
    assert persisted_task is not None
    assert persisted_task.status == "failed"


def test_run_task_execution_rejects_invalid_job_module_task_combination() -> None:
    task_id = _create_task_fixture(
        task_type="jd_summary",
        workspace_type="support",
        input_json={"target_role": "Platform engineer"},
    )

    with pytest.raises(TaskExecutionError, match="Task type jd_summary is not supported"):
        task_execution_service.run_task_execution(task_id)

    persisted_task = task_repository.get_task(task_id)
    assert persisted_task is not None
    assert persisted_task.status == "failed"



def test_run_task_execution_short_circuits_running_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_id = _create_task_fixture(goal="Who owns the project?")
    running_task = task_repository.update_task_status(task_id, next_status="running")

    assert running_task is not None
    monkeypatch.setattr(
        task_execution_service,
        "_execute_task_agent",
        lambda _task: pytest.fail("running tasks should not execute again"),
    )

    output = task_execution_service.run_task_execution(task_id)
    persisted_task = task_repository.get_task(task_id)

    assert output == {
        "task_id": task_id,
        "task_type": "research_summary",
        "worker": "arq",
        "status": "running",
        "skipped": True,
    }
    assert persisted_task is not None
    assert persisted_task.status == "running"
    assert task_repository.list_task_agent_runs(task_id) == []


def test_run_task_execution_returns_existing_output_for_completed_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_id = _create_task_fixture(goal="Who owns the project?")
    running_task = task_repository.update_task_status(task_id, next_status="running")

    assert running_task is not None
    expected_output = {
        "task_id": task_id,
        "task_type": "research_summary",
        "worker": "arq",
        "status": "completed",
        "agent_name": "workspace_research_agent",
        "agent_run_id": "agent-run-1",
        "result": {"module_type": "research"},
    }
    completed_task = task_repository.update_task_status(
        task_id,
        next_status="done",
        output_json=expected_output,
    )

    assert completed_task is not None
    monkeypatch.setattr(
        task_execution_service,
        "_execute_task_agent",
        lambda _task: pytest.fail("completed tasks should not execute again"),
    )

    output = task_execution_service.run_task_execution(task_id)

    assert output == expected_output
    assert task_repository.list_task_agent_runs(task_id) == []


def test_run_task_execution_short_circuits_failed_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_id = _create_task_fixture(goal="Who owns the project?")
    failed_task = task_repository.update_task_status(
        task_id,
        next_status="failed",
        error_message="Previous worker failure",
    )

    assert failed_task is not None
    monkeypatch.setattr(
        task_execution_service,
        "_execute_task_agent",
        lambda _task: pytest.fail("failed tasks should not execute again"),
    )

    output = task_execution_service.run_task_execution(task_id)
    persisted_task = task_repository.get_task(task_id)

    assert output == {
        "task_id": task_id,
        "task_type": "research_summary",
        "worker": "arq",
        "status": "failed",
        "skipped": True,
        "error_message": "Previous worker failure",
    }
    assert persisted_task is not None
    assert persisted_task.status == "failed"
    assert persisted_task.error_message == "Previous worker failure"
    assert task_repository.list_task_agent_runs(task_id) == []


def test_run_platform_task_worker_entrypoint_executes_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeRetriever:
        def retrieve(self, *, workspace_id: str, question: str) -> list[RetrievedChunk]:
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

    task_id = _create_task_fixture(goal="Who owns the project?")

    output = asyncio.run(run_platform_task({}, task_id))
    persisted_task = task_repository.get_task(task_id)

    assert output["task_id"] == task_id
    assert output["agent_name"] == "workspace_research_agent"
    assert output["result"]["module_type"] == "research"
    assert persisted_task is not None
    assert persisted_task.status == "done"

