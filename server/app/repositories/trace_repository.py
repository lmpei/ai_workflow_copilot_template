from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select

from app.core.database import session_scope
from app.models.trace import Trace


def create_trace(
    *,
    workspace_id: str,
    trace_type: str,
    request_json: dict,
    response_json: dict,
    metadata_json: dict | None = None,
    parent_trace_id: str | None = None,
    task_id: str | None = None,
    agent_run_id: str | None = None,
    tool_call_id: str | None = None,
    eval_run_id: str | None = None,
    error_message: str | None = None,
    latency_ms: int,
    token_input: int = 0,
    token_output: int = 0,
    estimated_cost: float = 0.0,
) -> Trace:
    trace = Trace(
        id=str(uuid4()),
        workspace_id=workspace_id,
        parent_trace_id=parent_trace_id,
        task_id=task_id,
        agent_run_id=agent_run_id,
        tool_call_id=tool_call_id,
        eval_run_id=eval_run_id,
        trace_type=trace_type,
        request_json=request_json,
        response_json=response_json,
        metadata_json=metadata_json or {},
        error_message=error_message,
        latency_ms=latency_ms,
        token_input=token_input,
        token_output=token_output,
        estimated_cost=estimated_cost,
        created_at=datetime.now(UTC),
    )
    with session_scope() as session:
        session.add(trace)
        session.flush()
        session.refresh(trace)
        return trace


def list_traces_for_workspace(workspace_id: str) -> list[Trace]:
    with session_scope() as session:
        statement = (
            select(Trace)
            .where(Trace.workspace_id == workspace_id)
            .order_by(Trace.created_at.asc())
        )
        result = session.scalars(statement)
        return list(result)


def list_traces_for_task(task_id: str) -> list[Trace]:
    with session_scope() as session:
        statement = select(Trace).where(Trace.task_id == task_id).order_by(Trace.created_at.asc())
        return list(session.scalars(statement))


def list_traces_for_agent_run(agent_run_id: str) -> list[Trace]:
    with session_scope() as session:
        statement = (
            select(Trace)
            .where(Trace.agent_run_id == agent_run_id)
            .order_by(Trace.created_at.asc())
        )
        return list(session.scalars(statement))


def list_traces_for_tool_call(tool_call_id: str) -> list[Trace]:
    with session_scope() as session:
        statement = (
            select(Trace)
            .where(Trace.tool_call_id == tool_call_id)
            .order_by(Trace.created_at.asc())
        )
        return list(session.scalars(statement))


def list_traces_for_eval_run(eval_run_id: str) -> list[Trace]:
    with session_scope() as session:
        statement = (
            select(Trace)
            .where(Trace.eval_run_id == eval_run_id)
            .order_by(Trace.created_at.asc())
        )
        return list(session.scalars(statement))


def list_child_traces(parent_trace_id: str) -> list[Trace]:
    with session_scope() as session:
        statement = (
            select(Trace)
            .where(Trace.parent_trace_id == parent_trace_id)
            .order_by(Trace.created_at.asc())
        )
        return list(session.scalars(statement))
