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
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
    failed_at: datetime | None = None,
    failure_stage: str | None = None,
    trace_events_json: list[dict[str, object]] | None = None,
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
        started_at=started_at,
        completed_at=completed_at,
        failed_at=failed_at,
        failure_stage=failure_stage,
        trace_events_json=trace_events_json or [],
        generated_at=generated_at,
        created_at=now,
        updated_at=now,
    )
    with session_scope() as session:
        session.add(run)
        session.flush()
        session.refresh(run)
        return run


def create_queued_ai_hot_tracker_tracking_run(
    *,
    workspace_id: str,
    previous_run_id: str | None,
    created_by: str,
    trigger_kind: str,
    title: str,
    question: str,
    profile_snapshot_json: dict[str, object],
    output_json: dict[str, object],
    delta_json: dict[str, object],
    trace_events_json: list[dict[str, object]],
    generated_at: datetime,
) -> AiHotTrackerTrackingRun:
    now = datetime.now(UTC)
    run = AiHotTrackerTrackingRun(
        id=str(uuid4()),
        workspace_id=workspace_id,
        previous_run_id=previous_run_id,
        created_by=created_by,
        trigger_kind=trigger_kind,
        status="queued",
        title=title,
        question=question,
        profile_snapshot_json=profile_snapshot_json,
        output_json=output_json,
        source_catalog_json=[],
        source_items_json=[],
        source_failures_json=[],
        source_set_json={},
        delta_json=delta_json,
        follow_ups_json=[],
        degraded_reason=None,
        error_message=None,
        started_at=None,
        completed_at=None,
        failed_at=None,
        failure_stage=None,
        trace_events_json=trace_events_json,
        generated_at=generated_at,
        created_at=now,
        updated_at=now,
    )
    with session_scope() as session:
        session.add(run)
        session.flush()
        session.refresh(run)
        return run


def update_ai_hot_tracker_tracking_run_runtime(
    *,
    run_id: str,
    status: str,
    title: str | None = None,
    question: str | None = None,
    output_json: dict[str, object] | None = None,
    source_catalog_json: list[dict[str, object]] | None = None,
    source_items_json: list[dict[str, object]] | None = None,
    source_failures_json: list[dict[str, object]] | None = None,
    source_set_json: dict[str, object] | None = None,
    delta_json: dict[str, object] | None = None,
    degraded_reason: str | None = None,
    error_message: str | None = None,
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
    failed_at: datetime | None = None,
    failure_stage: str | None = None,
    trace_events_json: list[dict[str, object]] | None = None,
    generated_at: datetime | None = None,
) -> AiHotTrackerTrackingRun | None:
    with session_scope() as session:
        run = session.get(AiHotTrackerTrackingRun, run_id)
        if run is None:
            return None

        run.status = status
        if title is not None:
            run.title = title
        if question is not None:
            run.question = question
        if output_json is not None:
            run.output_json = output_json
        if source_catalog_json is not None:
            run.source_catalog_json = source_catalog_json
        if source_items_json is not None:
            run.source_items_json = source_items_json
        if source_failures_json is not None:
            run.source_failures_json = source_failures_json
        if source_set_json is not None:
            run.source_set_json = source_set_json
        if delta_json is not None:
            run.delta_json = delta_json
        run.degraded_reason = degraded_reason
        run.error_message = error_message
        if started_at is not None:
            run.started_at = started_at
        if completed_at is not None:
            run.completed_at = completed_at
        if failed_at is not None:
            run.failed_at = failed_at
        run.failure_stage = failure_stage
        if trace_events_json is not None:
            run.trace_events_json = trace_events_json
        if generated_at is not None:
            run.generated_at = generated_at
        run.updated_at = datetime.now(UTC)
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
            .where(AiHotTrackerTrackingRun.status.in_(["completed", "degraded", "failed"]))
            .order_by(AiHotTrackerTrackingRun.generated_at.desc(), AiHotTrackerTrackingRun.updated_at.desc())
            .limit(1)
        )
        return session.scalar(statement)


def get_ai_hot_tracker_tracking_run(
    *,
    run_id: str,
) -> AiHotTrackerTrackingRun | None:
    with session_scope() as session:
        statement = select(AiHotTrackerTrackingRun).where(
            AiHotTrackerTrackingRun.id == run_id
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
