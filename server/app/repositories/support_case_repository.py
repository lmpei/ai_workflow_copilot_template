from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select

from app.core.database import session_scope
from app.models.support_case import SupportCase
from app.models.support_case_event import SupportCaseEvent
from app.models.workspace_member import WorkspaceMember


def get_support_case(case_id: str) -> SupportCase | None:
    with session_scope() as session:
        return session.get(SupportCase, case_id)


def get_support_case_for_user(case_id: str, user_id: str) -> SupportCase | None:
    with session_scope() as session:
        statement = (
            select(SupportCase)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == SupportCase.workspace_id)
            .where(
                SupportCase.id == case_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        return session.scalar(statement)


def list_workspace_support_cases(workspace_id: str, user_id: str) -> list[SupportCase]:
    with session_scope() as session:
        statement = (
            select(SupportCase)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == SupportCase.workspace_id)
            .where(
                SupportCase.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
            .order_by(SupportCase.updated_at.desc(), SupportCase.created_at.desc())
        )
        return list(session.scalars(statement))


def list_support_case_events(case_id: str) -> list[SupportCaseEvent]:
    with session_scope() as session:
        statement = (
            select(SupportCaseEvent)
            .where(SupportCaseEvent.support_case_id == case_id)
            .order_by(SupportCaseEvent.created_at.desc())
        )
        return list(session.scalars(statement))


def get_support_case_event_by_task_id(task_id: str) -> SupportCaseEvent | None:
    with session_scope() as session:
        statement = select(SupportCaseEvent).where(SupportCaseEvent.task_id == task_id)
        return session.scalar(statement)


def create_support_case(
    *,
    workspace_id: str,
    created_by: str,
    title: str,
    status: str,
    latest_task_id: str,
    latest_task_type: str,
    latest_input_json: dict[str, object],
    latest_result_json: dict[str, object],
    latest_summary: str,
    latest_recommended_owner: str | None,
    latest_evidence_status: str | None,
) -> SupportCase:
    now = datetime.now(UTC)
    case = SupportCase(
        id=str(uuid4()),
        workspace_id=workspace_id,
        created_by=created_by,
        title=title,
        status=status,
        latest_task_id=latest_task_id,
        latest_task_type=latest_task_type,
        latest_input_json=latest_input_json,
        latest_result_json=latest_result_json,
        latest_summary=latest_summary,
        latest_recommended_owner=latest_recommended_owner,
        latest_evidence_status=latest_evidence_status,
        event_count=1,
        created_at=now,
        updated_at=now,
    )
    with session_scope() as session:
        session.add(case)
        session.flush()
        session.refresh(case)
        return case


def create_support_case_event(
    *,
    support_case_id: str,
    task_id: str,
    task_type: str,
    event_kind: str,
    title: str,
    summary: str,
    case_status: str,
    recommended_owner: str | None,
    evidence_status: str | None,
    should_escalate: bool,
    needs_manual_review: bool,
    follow_up_notes: str | None,
    created_at: datetime,
) -> SupportCaseEvent:
    event = SupportCaseEvent(
        id=str(uuid4()),
        support_case_id=support_case_id,
        task_id=task_id,
        task_type=task_type,
        event_kind=event_kind,
        title=title,
        summary=summary,
        case_status=case_status,
        recommended_owner=recommended_owner,
        evidence_status=evidence_status,
        should_escalate=should_escalate,
        needs_manual_review=needs_manual_review,
        follow_up_notes=follow_up_notes,
        created_at=created_at,
    )
    with session_scope() as session:
        session.add(event)
        session.flush()
        session.refresh(event)
        return event


def update_support_case_snapshot(
    case_id: str,
    *,
    title: str | None = None,
    status: str | None = None,
    latest_task_id: str | None = None,
    latest_task_type: str | None = None,
    latest_input_json: dict[str, object] | None = None,
    latest_result_json: dict[str, object] | None = None,
    latest_summary: str | None = None,
    latest_recommended_owner: str | None = None,
    latest_evidence_status: str | None = None,
    event_count: int | None = None,
) -> SupportCase | None:
    with session_scope() as session:
        case = session.get(SupportCase, case_id)
        if case is None:
            return None

        if title is not None:
            case.title = title
        if status is not None:
            case.status = status
        if latest_task_id is not None:
            case.latest_task_id = latest_task_id
        if latest_task_type is not None:
            case.latest_task_type = latest_task_type
        if latest_input_json is not None:
            case.latest_input_json = latest_input_json
        if latest_result_json is not None:
            case.latest_result_json = latest_result_json
        if latest_summary is not None:
            case.latest_summary = latest_summary
        case.latest_recommended_owner = latest_recommended_owner
        case.latest_evidence_status = latest_evidence_status
        if event_count is not None:
            case.event_count = event_count
        case.updated_at = datetime.now(UTC)

        session.add(case)
        session.flush()
        session.refresh(case)
        return case
