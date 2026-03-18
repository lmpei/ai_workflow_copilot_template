from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select

from app.core.database import session_scope
from app.models.agent_run import (
    AGENT_RUN_STATUS_PENDING,
    AGENT_RUN_STATUS_RUNNING,
    AgentRun,
    can_transition_agent_run_status,
    is_valid_agent_run_status,
)
from app.models.task import (
    TASK_STATUS_PENDING,
    Task,
    can_transition_task_status,
    is_valid_task_status,
)
from app.models.tool_call import (
    TOOL_CALL_STATUS_PENDING,
    ToolCall,
    can_transition_tool_call_status,
    is_valid_tool_call_status,
)
from app.models.workspace_member import WorkspaceMember


def create_task(
    *,
    workspace_id: str,
    task_type: str,
    created_by: str,
    input_json: dict[str, object] | None = None,
    control_json: dict[str, object] | None = None,
    status: str = TASK_STATUS_PENDING,
) -> Task:
    if not is_valid_task_status(status):
        raise ValueError(f"Unsupported task status: {status}")

    now = datetime.now(UTC)
    task = Task(
        id=str(uuid4()),
        workspace_id=workspace_id,
        task_type=task_type,
        status=status,
        created_by=created_by,
        input_json=input_json or {},
        output_json={},
        control_json=control_json or {},
        error_message=None,
        created_at=now,
        updated_at=now,
    )
    with session_scope() as session:
        session.add(task)
        session.flush()
        session.refresh(task)
        return task


def get_task(task_id: str) -> Task | None:
    with session_scope() as session:
        return session.get(Task, task_id)


def get_task_for_user(task_id: str, user_id: str) -> Task | None:
    with session_scope() as session:
        statement = (
            select(Task)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Task.workspace_id)
            .where(
                Task.id == task_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        return session.scalar(statement)


def list_workspace_tasks(workspace_id: str, user_id: str) -> list[Task]:
    with session_scope() as session:
        statement = (
            select(Task)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Task.workspace_id)
            .where(
                Task.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
            .order_by(Task.created_at.asc())
        )
        return list(session.scalars(statement))


def update_task_status(
    task_id: str,
    *,
    next_status: str,
    output_json: dict[str, object] | None = None,
    control_json: dict[str, object] | None = None,
    error_message: str | None = None,
) -> Task | None:
    if not is_valid_task_status(next_status):
        raise ValueError(f"Unsupported task status: {next_status}")

    with session_scope() as session:
        task = session.get(Task, task_id)
        if task is None:
            return None

        if not can_transition_task_status(task.status, next_status):
            raise ValueError(f"Invalid task status transition: {task.status} -> {next_status}")

        task.status = next_status
        task.updated_at = datetime.now(UTC)
        if output_json is not None:
            task.output_json = output_json
        if control_json is not None:
            task.control_json = control_json
        if error_message is not None:
            task.error_message = error_message
        elif next_status != "failed":
            task.error_message = None

        session.add(task)
        session.flush()
        session.refresh(task)
        return task


def create_agent_run(
    *,
    task_id: str,
    agent_name: str,
    status: str = AGENT_RUN_STATUS_PENDING,
) -> AgentRun:
    if not is_valid_agent_run_status(status):
        raise ValueError(f"Unsupported agent run status: {status}")

    now = datetime.now(UTC)
    agent_run = AgentRun(
        id=str(uuid4()),
        task_id=task_id,
        agent_name=agent_name,
        status=status,
        final_output=None,
        created_at=now,
        started_at=now if status == AGENT_RUN_STATUS_RUNNING else None,
        ended_at=None,
    )
    with session_scope() as session:
        session.add(agent_run)
        session.flush()
        session.refresh(agent_run)
        return agent_run


def get_agent_run(agent_run_id: str) -> AgentRun | None:
    with session_scope() as session:
        return session.get(AgentRun, agent_run_id)


def list_task_agent_runs(task_id: str) -> list[AgentRun]:
    with session_scope() as session:
        statement = (
            select(AgentRun)
            .where(AgentRun.task_id == task_id)
            .order_by(AgentRun.created_at.asc())
        )
        return list(session.scalars(statement))


def update_agent_run_status(
    agent_run_id: str,
    *,
    next_status: str,
    final_output: dict[str, object] | None = None,
) -> AgentRun | None:
    if not is_valid_agent_run_status(next_status):
        raise ValueError(f"Unsupported agent run status: {next_status}")

    with session_scope() as session:
        agent_run = session.get(AgentRun, agent_run_id)
        if agent_run is None:
            return None

        if not can_transition_agent_run_status(agent_run.status, next_status):
            raise ValueError(
                f"Invalid agent run status transition: {agent_run.status} -> {next_status}",
            )

        agent_run.status = next_status
        now = datetime.now(UTC)
        if next_status == AGENT_RUN_STATUS_RUNNING and agent_run.started_at is None:
            agent_run.started_at = now
        if next_status in {"completed", "failed"}:
            agent_run.ended_at = now
        if final_output is not None:
            agent_run.final_output = final_output

        session.add(agent_run)
        session.flush()
        session.refresh(agent_run)
        return agent_run


def create_tool_call(
    *,
    agent_run_id: str,
    tool_name: str,
    tool_input_json: dict[str, object] | None = None,
    status: str = TOOL_CALL_STATUS_PENDING,
) -> ToolCall:
    if not is_valid_tool_call_status(status):
        raise ValueError(f"Unsupported tool call status: {status}")

    tool_call = ToolCall(
        id=str(uuid4()),
        agent_run_id=agent_run_id,
        tool_name=tool_name,
        tool_input_json=tool_input_json or {},
        tool_output_json=None,
        status=status,
        latency_ms=0,
    )
    with session_scope() as session:
        session.add(tool_call)
        session.flush()
        session.refresh(tool_call)
        return tool_call


def get_tool_call(tool_call_id: str) -> ToolCall | None:
    with session_scope() as session:
        return session.get(ToolCall, tool_call_id)


def list_agent_run_tool_calls(agent_run_id: str) -> list[ToolCall]:
    with session_scope() as session:
        statement = (
            select(ToolCall)
            .where(ToolCall.agent_run_id == agent_run_id)
            .order_by(ToolCall.created_at.asc())
        )
        return list(session.scalars(statement))


def update_tool_call_status(
    tool_call_id: str,
    *,
    next_status: str,
    tool_output_json: dict[str, object] | None = None,
    latency_ms: int | None = None,
) -> ToolCall | None:
    if not is_valid_tool_call_status(next_status):
        raise ValueError(f"Unsupported tool call status: {next_status}")

    with session_scope() as session:
        tool_call = session.get(ToolCall, tool_call_id)
        if tool_call is None:
            return None

        if not can_transition_tool_call_status(tool_call.status, next_status):
            raise ValueError(
                f"Invalid tool call status transition: {tool_call.status} -> {next_status}",
            )

        tool_call.status = next_status
        if tool_output_json is not None:
            tool_call.tool_output_json = tool_output_json
        if latency_ms is not None:
            tool_call.latency_ms = latency_ms

        session.add(tool_call)
        session.flush()
        session.refresh(tool_call)
        return tool_call
