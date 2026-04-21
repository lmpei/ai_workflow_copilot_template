from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select

from app.core.database import session_scope
from app.models.ai_hot_tracker_tracking_run import AiHotTrackerTrackingRun
from app.models.workspace_member import WorkspaceMember


def create_ai_hot_tracker_tracking_run(
    *,
    workspace_id: str,
    previous_run_id: str | None,
    created_by: str,
    trigger_kind: str,
    status: str,
    title: str,
    question: str,
    profile_snapshot_json: dict[str, object],
    output_json: dict[str, object],
    source_catalog_json: list[dict[str, object]],
    source_items_json: list[dict[str, object]],
    source_failures_json: list[dict[str, object]],
    source_set_json: dict[str, object],
    delta_json: dict[str, object],
    follow_ups_json: list[dict[str, object]],
    degraded_reason: str | None,
    error_message: str | None,
    generated_at: datetime,
) -> AiHotTrackerTrackingRun:
    now = datetime.now(UTC)
    run = AiHotTrackerTrackingRun(
        id=str(uuid4()),
        workspace_id=workspace_id,
        previous_run_id=previous_run_id,
        created_by=created_by,
        trigger_kind=trigger_kind,
        status=status,
        title=title,
        question=question,
        profile_snapshot_json=profile_snapshot_json,
        output_json=output_json,
        source_catalog_json=source_catalog_json,
        source_items_json=source_items_json,
        source_failures_json=source_failures_json,
        source_set_json=source_set_json,
        delta_json=delta_json,
        follow_ups_json=follow_ups_json,
        degraded_reason=degraded_reason,
        error_message=error_message,
        generated_at=generated_at,
        created_at=now,
        updated_at=now,
    )
    with session_scope() as session:
        session.add(run)
        session.flush()
        session.refresh(run)
        return run


def list_workspace_ai_hot_tracker_tracking_runs(
    *,
    workspace_id: str,
    user_id: str,
    limit: int = 12,
) -> list[AiHotTrackerTrackingRun]:
    with session_scope() as session:
        statement = (
            select(AiHotTrackerTrackingRun)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == AiHotTrackerTrackingRun.workspace_id)
            .where(
                AiHotTrackerTrackingRun.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
            .order_by(AiHotTrackerTrackingRun.generated_at.desc(), AiHotTrackerTrackingRun.updated_at.desc())
            .limit(limit)
        )
        return list(session.scalars(statement))


def get_ai_hot_tracker_tracking_run_for_user(
    *,
    run_id: str,
    user_id: str,
) -> AiHotTrackerTrackingRun | None:
    with session_scope() as session:
        statement = (
            select(AiHotTrackerTrackingRun)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == AiHotTrackerTrackingRun.workspace_id)
            .where(
                AiHotTrackerTrackingRun.id == run_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        return session.scalar(statement)


def get_latest_workspace_ai_hot_tracker_tracking_run(
    *,
    workspace_id: str,
) -> AiHotTrackerTrackingRun | None:
    with session_scope() as session:
        statement = (
            select(AiHotTrackerTrackingRun)
            .where(AiHotTrackerTrackingRun.workspace_id == workspace_id)
            .order_by(AiHotTrackerTrackingRun.generated_at.desc(), AiHotTrackerTrackingRun.updated_at.desc())
            .limit(1)
        )
        return session.scalar(statement)


def update_ai_hot_tracker_tracking_run_follow_ups(
    *,
    run_id: str,
    user_id: str,
    follow_ups_json: list[dict[str, object]],
) -> AiHotTrackerTrackingRun | None:
    with session_scope() as session:
        statement = (
            select(AiHotTrackerTrackingRun)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == AiHotTrackerTrackingRun.workspace_id)
            .where(
                AiHotTrackerTrackingRun.id == run_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        run = session.scalar(statement)
        if run is None:
            return None

        run.follow_ups_json = follow_ups_json
        run.updated_at = datetime.now(UTC)
        session.add(run)
        session.flush()
        session.refresh(run)
        return run


def delete_ai_hot_tracker_tracking_run(*, run_id: str, user_id: str) -> bool:
    with session_scope() as session:
        statement = (
            select(AiHotTrackerTrackingRun)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == AiHotTrackerTrackingRun.workspace_id)
            .where(
                AiHotTrackerTrackingRun.id == run_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        run = session.scalar(statement)
        if run is None:
            return False

        session.delete(run)
        session.flush()
        return True
