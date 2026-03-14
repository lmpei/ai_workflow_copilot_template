import asyncio
from uuid import uuid4

import pytest

from app.core.database import reset_database_for_tests
from app.repositories.task_repository import create_task, get_task
from app.repositories.user_repository import create_user
from app.repositories.workspace_repository import create_workspace
from app.schemas.workspace import WorkspaceCreate
from app.services import task_execution_service
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


def _create_task_fixture() -> str:
    unique_suffix = uuid4().hex
    user = create_user(
        email=f"phase3-worker-{unique_suffix}@example.com",
        password_hash="not-used-in-this-test",
        name="Phase 3 Worker",
    )
    workspace = create_workspace(
        WorkspaceCreate(name="Phase 3 Worker Workspace", type="research"),
        owner_id=user.id,
    )
    task = create_task(
        workspace_id=workspace.id,
        task_type="research_summary",
        created_by=user.id,
        input_json={"goal": "summarize"},
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


def test_run_task_execution_marks_task_done_and_persists_output() -> None:
    task_id = _create_task_fixture()

    output = task_execution_service.run_task_execution(task_id)
    persisted_task = get_task(task_id)

    assert output["worker"] == "arq"
    assert persisted_task is not None
    assert persisted_task.status == "done"
    assert persisted_task.output_json == output


def test_run_task_execution_marks_task_failed_when_execution_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_id = _create_task_fixture()

    def fail_placeholder(_task: object) -> dict[str, object]:
        raise RuntimeError("placeholder failed")

    monkeypatch.setattr(task_execution_service, "_build_placeholder_task_output", fail_placeholder)

    with pytest.raises(TaskExecutionError, match="Task execution failed"):
        task_execution_service.run_task_execution(task_id)

    persisted_task = get_task(task_id)
    assert persisted_task is not None
    assert persisted_task.status == "failed"
    assert persisted_task.error_message == "placeholder failed"


def test_run_platform_task_worker_entrypoint_executes_task() -> None:
    task_id = _create_task_fixture()

    output = asyncio.run(run_platform_task({}, task_id))
    persisted_task = get_task(task_id)

    assert output["task_id"] == task_id
    assert persisted_task is not None
    assert persisted_task.status == "done"
