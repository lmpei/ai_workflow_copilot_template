from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select

from app.core.database import session_scope
from app.models.ai_frontier_research_record import AiFrontierResearchRecord
from app.models.workspace_member import WorkspaceMember


def create_ai_frontier_research_record(
    *,
    workspace_id: str,
    conversation_id: str | None,
    source_run_id: str | None,
    source_trace_id: str | None,
    created_by: str,
    title: str,
    question: str,
    frontier_summary: str,
    trend_judgment: str,
    themes_json: list[dict[str, object]],
    events_json: list[dict[str, object]],
    project_cards_json: list[dict[str, object]],
    reference_sources_json: list[dict[str, object]],
    source_set_json: dict[str, object],
) -> AiFrontierResearchRecord:
    now = datetime.now(UTC)
    record = AiFrontierResearchRecord(
        id=str(uuid4()),
        workspace_id=workspace_id,
        conversation_id=conversation_id,
        source_run_id=source_run_id,
        source_trace_id=source_trace_id,
        created_by=created_by,
        title=title,
        question=question,
        frontier_summary=frontier_summary,
        trend_judgment=trend_judgment,
        themes_json=themes_json,
        events_json=events_json,
        project_cards_json=project_cards_json,
        reference_sources_json=reference_sources_json,
        source_set_json=source_set_json,
        created_at=now,
        updated_at=now,
    )
    with session_scope() as session:
        session.add(record)
        session.flush()
        session.refresh(record)
        return record


def get_ai_frontier_research_record(record_id: str) -> AiFrontierResearchRecord | None:
    with session_scope() as session:
        return session.get(AiFrontierResearchRecord, record_id)


def get_ai_frontier_research_record_for_user(record_id: str, user_id: str) -> AiFrontierResearchRecord | None:
    with session_scope() as session:
        statement = (
            select(AiFrontierResearchRecord)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == AiFrontierResearchRecord.workspace_id)
            .where(
                AiFrontierResearchRecord.id == record_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        return session.scalar(statement)


def get_ai_frontier_research_record_by_source_run_id(source_run_id: str) -> AiFrontierResearchRecord | None:
    with session_scope() as session:
        statement = (
            select(AiFrontierResearchRecord)
            .where(AiFrontierResearchRecord.source_run_id == source_run_id)
            .order_by(AiFrontierResearchRecord.created_at.desc())
            .limit(1)
        )
        return session.scalar(statement)


def list_workspace_ai_frontier_research_records(
    *,
    workspace_id: str,
    user_id: str,
    limit: int = 12,
) -> list[AiFrontierResearchRecord]:
    with session_scope() as session:
        statement = (
            select(AiFrontierResearchRecord)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == AiFrontierResearchRecord.workspace_id)
            .where(
                AiFrontierResearchRecord.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
            .order_by(AiFrontierResearchRecord.created_at.desc(), AiFrontierResearchRecord.updated_at.desc())
            .limit(limit)
        )
        return list(session.scalars(statement))


def update_ai_frontier_research_record(
    *,
    record_id: str,
    user_id: str,
    title: str,
    question: str,
    frontier_summary: str,
    trend_judgment: str,
    themes_json: list[dict[str, object]],
    events_json: list[dict[str, object]],
    project_cards_json: list[dict[str, object]],
    reference_sources_json: list[dict[str, object]],
    source_set_json: dict[str, object],
) -> AiFrontierResearchRecord | None:
    with session_scope() as session:
        statement = (
            select(AiFrontierResearchRecord)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == AiFrontierResearchRecord.workspace_id)
            .where(
                AiFrontierResearchRecord.id == record_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        record = session.scalar(statement)
        if record is None:
            return None

        record.title = title
        record.question = question
        record.frontier_summary = frontier_summary
        record.trend_judgment = trend_judgment
        record.themes_json = themes_json
        record.events_json = events_json
        record.project_cards_json = project_cards_json
        record.reference_sources_json = reference_sources_json
        record.source_set_json = source_set_json
        record.updated_at = datetime.now(UTC)
        session.add(record)
        session.flush()
        session.refresh(record)
        return record


def delete_ai_frontier_research_record(*, record_id: str, user_id: str) -> bool:
    with session_scope() as session:
        statement = (
            select(AiFrontierResearchRecord)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == AiFrontierResearchRecord.workspace_id)
            .where(
                AiFrontierResearchRecord.id == record_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        record = session.scalar(statement)
        if record is None:
            return False

        session.delete(record)
        session.flush()
        return True
