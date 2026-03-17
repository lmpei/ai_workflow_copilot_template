from uuid import uuid4

import pytest

from app.core.database import reset_database_for_tests
from app.models.agent_run import AGENT_RUN_STATUS_RUNNING
from app.models.task import TASK_STATUS_PENDING
from app.models.tool_call import TOOL_CALL_STATUS_PENDING
from app.repositories.task_repository import (
    create_agent_run,
    create_task,
    create_tool_call,
    get_task,
    get_task_for_user,
    list_agent_run_tool_calls,
    list_task_agent_runs,
    list_workspace_tasks,
    update_agent_run_status,
    update_task_status,
    update_tool_call_status,
)
from app.repositories.user_repository import create_user
from app.repositories.workspace_repository import create_workspace
from app.schemas.workspace import WorkspaceCreate


@pytest.fixture(autouse=True)
def reset_database() -> None:
    reset_database_for_tests()


def _create_workspace_fixture() -> tuple[str, str]:
    unique_suffix = uuid4().hex
    user = create_user(
        email=f"phase3-owner-{unique_suffix}@example.com",
        password_hash="not-used-in-this-test",
        name="Phase 3 Owner",
    )
    workspace = create_workspace(
        WorkspaceCreate(name="Phase 3 Workspace", module_type="research"),
        owner_id=user.id,
    )
    return user.id, workspace.id


def test_task_repository_creates_and_lists_workspace_tasks() -> None:
    user_id, workspace_id = _create_workspace_fixture()

    task = create_task(
        workspace_id=workspace_id,
        task_type="research_summary",
        created_by=user_id,
        input_json={"goal": "summarize indexed content"},
    )

    persisted = get_task(task.id)
    scoped = get_task_for_user(task.id, user_id)
    workspace_tasks = list_workspace_tasks(workspace_id, user_id)

    assert task.status == TASK_STATUS_PENDING
    assert persisted is not None
    assert persisted.input_json["goal"] == "summarize indexed content"
    assert scoped is not None
    assert [item.id for item in workspace_tasks] == [task.id]


def test_task_repository_persists_task_results_and_rejects_invalid_transitions() -> None:
    user_id, workspace_id = _create_workspace_fixture()
    task = create_task(
        workspace_id=workspace_id,
        task_type="workspace_report",
        created_by=user_id,
    )

    running = update_task_status(task.id, next_status="running")
    done = update_task_status(
        task.id,
        next_status="done",
        output_json={"summary": "ready"},
    )

    assert running is not None
    assert running.status == "running"
    assert done is not None
    assert done.status == "done"
    assert done.output_json == {"summary": "ready"}

    with pytest.raises(ValueError, match="Invalid task status transition"):
        update_task_status(task.id, next_status="pending")

    with pytest.raises(ValueError, match="Unsupported task status"):
        update_task_status(task.id, next_status="queued")


def test_agent_runs_track_started_and_ended_timestamps() -> None:
    user_id, workspace_id = _create_workspace_fixture()
    task = create_task(
        workspace_id=workspace_id,
        task_type="research_summary",
        created_by=user_id,
    )

    pending_run = create_agent_run(task_id=task.id, agent_name="workspace_research_agent")
    running_run = update_agent_run_status(pending_run.id, next_status=AGENT_RUN_STATUS_RUNNING)
    completed_run = update_agent_run_status(
        pending_run.id,
        next_status="completed",
        final_output={"summary": "done"},
    )

    persisted_runs = list_task_agent_runs(task.id)

    assert pending_run.started_at is None
    assert running_run is not None
    assert running_run.started_at is not None
    assert completed_run is not None
    assert completed_run.ended_at is not None
    assert completed_run.final_output == {"summary": "done"}
    assert [item.id for item in persisted_runs] == [pending_run.id]


def test_tool_calls_persist_outputs_latency_and_reject_invalid_transitions() -> None:
    user_id, workspace_id = _create_workspace_fixture()
    task = create_task(
        workspace_id=workspace_id,
        task_type="research_summary",
        created_by=user_id,
    )
    agent_run = create_agent_run(
        task_id=task.id,
        agent_name="workspace_research_agent",
        status=AGENT_RUN_STATUS_RUNNING,
    )

    tool_call = create_tool_call(
        agent_run_id=agent_run.id,
        tool_name="search_documents",
        tool_input_json={"query": "apollo"},
    )
    running_call = update_tool_call_status(tool_call.id, next_status="running")
    completed_call = update_tool_call_status(
        tool_call.id,
        next_status="completed",
        tool_output_json={"hits": 1},
        latency_ms=42,
    )

    persisted_calls = list_agent_run_tool_calls(agent_run.id)

    assert tool_call.status == TOOL_CALL_STATUS_PENDING
    assert running_call is not None
    assert running_call.status == "running"
    assert completed_call is not None
    assert completed_call.tool_output_json == {"hits": 1}
    assert completed_call.latency_ms == 42
    assert [item.id for item in persisted_calls] == [tool_call.id]

    with pytest.raises(ValueError, match="Invalid tool call status transition"):
        update_tool_call_status(tool_call.id, next_status="pending")

