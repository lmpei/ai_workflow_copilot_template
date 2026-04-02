from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import desc, select

from app.core.database import session_scope
from app.models.research_analysis_run import (
    RESEARCH_ANALYSIS_RUN_STATUS_PENDING,
    RESEARCH_ANALYSIS_RUN_STATUS_RUNNING,
    ResearchAnalysisRun,
    can_transition_research_analysis_run_status,
    is_valid_research_analysis_run_status,
)
from app.models.workspace_member import WorkspaceMember

_TERMINAL_MEMORY_STATUSES = ("completed", "degraded")


def create_research_analysis_run(
    *,
    workspace_id: str,
    conversation_id: str,
    created_by: str,
    question: str,
    mode: str = "research_tool_assisted",
    status: str = RESEARCH_ANALYSIS_RUN_STATUS_PENDING,
    resumed_from_run_id: str | None = None,
) -> ResearchAnalysisRun:
    if not is_valid_research_analysis_run_status(status):
        raise ValueError(f"Unsupported research analysis run status: {status}")

    now = datetime.now(UTC)
    run = ResearchAnalysisRun(
        id=str(uuid4()),
        workspace_id=workspace_id,
        conversation_id=conversation_id,
        created_by=created_by,
        status=status,
        question=question,
        mode=mode,
        resumed_from_run_id=resumed_from_run_id,
        prompt=None,
        answer=None,
        trace_id=None,
        sources_json=[],
        tool_steps_json=[],
        run_memory_json={},
        analysis_focus=None,
        search_query=None,
        degraded_reason=None,
        error_message=None,
        created_at=now,
        started_at=now if status == RESEARCH_ANALYSIS_RUN_STATUS_RUNNING else None,
        completed_at=None,
        updated_at=now,
    )
    with session_scope() as session:
        session.add(run)
        session.flush()
        session.refresh(run)
        return run


def get_research_analysis_run(run_id: str) -> ResearchAnalysisRun | None:
    with session_scope() as session:
        return session.get(ResearchAnalysisRun, run_id)


def get_research_analysis_run_for_user(run_id: str, user_id: str) -> ResearchAnalysisRun | None:
    with session_scope() as session:
        statement = (
            select(ResearchAnalysisRun)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == ResearchAnalysisRun.workspace_id)
            .where(
                ResearchAnalysisRun.id == run_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        return session.scalar(statement)


def get_latest_resumable_research_analysis_run(
    *,
    conversation_id: str,
    user_id: str,
) -> ResearchAnalysisRun | None:
    with session_scope() as session:
        statement = (
            select(ResearchAnalysisRun)
            .where(
                ResearchAnalysisRun.conversation_id == conversation_id,
                ResearchAnalysisRun.created_by == user_id,
                ResearchAnalysisRun.status.in_(_TERMINAL_MEMORY_STATUSES),
            )
            .order_by(desc(ResearchAnalysisRun.completed_at), desc(ResearchAnalysisRun.updated_at))
            .limit(1)
        )
        return session.scalar(statement)


def list_workspace_research_analysis_runs(
    workspace_id: str,
    user_id: str,
    *,
    limit: int = 20,
) -> list[ResearchAnalysisRun]:
    with session_scope() as session:
        statement = (
            select(ResearchAnalysisRun)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == ResearchAnalysisRun.workspace_id)
            .where(
                ResearchAnalysisRun.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
            .order_by(ResearchAnalysisRun.created_at.desc(), ResearchAnalysisRun.updated_at.desc())
            .limit(limit)
        )
        return list(session.scalars(statement))


def update_research_analysis_run(
    run_id: str,
    *,
    next_status: str,
    prompt: str | None = None,
    answer: str | None = None,
    trace_id: str | None = None,
    sources_json: list[dict[str, object]] | None = None,
    tool_steps_json: list[dict[str, object]] | None = None,
    run_memory_json: dict[str, object] | None = None,
    analysis_focus: str | None = None,
    search_query: str | None = None,
    degraded_reason: str | None = None,
    error_message: str | None = None,
) -> ResearchAnalysisRun | None:
    if not is_valid_research_analysis_run_status(next_status):
        raise ValueError(f"Unsupported research analysis run status: {next_status}")

    with session_scope() as session:
        run = session.get(ResearchAnalysisRun, run_id)
        if run is None:
            return None

        if not can_transition_research_analysis_run_status(run.status, next_status):
            raise ValueError(f"Invalid research analysis run transition: {run.status} -> {next_status}")

        now = datetime.now(UTC)
        run.status = next_status
        run.updated_at = now
        if next_status == RESEARCH_ANALYSIS_RUN_STATUS_RUNNING and run.started_at is None:
            run.started_at = now
        if next_status in {"completed", "degraded", "failed"}:
            run.completed_at = now
        if prompt is not None:
            run.prompt = prompt
        if answer is not None:
            run.answer = answer
        if trace_id is not None:
            run.trace_id = trace_id
        if sources_json is not None:
            run.sources_json = sources_json
        if tool_steps_json is not None:
            run.tool_steps_json = tool_steps_json
        if run_memory_json is not None:
            run.run_memory_json = run_memory_json
        if analysis_focus is not None:
            run.analysis_focus = analysis_focus
        if search_query is not None:
            run.search_query = search_query
        run.degraded_reason = degraded_reason
        if error_message is not None:
            run.error_message = error_message
        elif next_status != "failed":
            run.error_message = None

        session.add(run)
        session.flush()
        session.refresh(run)
        return run
