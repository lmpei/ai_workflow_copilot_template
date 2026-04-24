from datetime import UTC, datetime

from sqlalchemy import select

from app.core.database import session_scope
from app.models.ai_hot_tracker_tracking_state import AiHotTrackerTrackingState


def get_ai_hot_tracker_tracking_state(
    *,
    workspace_id: str,
) -> AiHotTrackerTrackingState | None:
    with session_scope() as session:
        statement = select(AiHotTrackerTrackingState).where(
            AiHotTrackerTrackingState.workspace_id == workspace_id
        )
        return session.scalar(statement)


def upsert_ai_hot_tracker_tracking_state(
    *,
    workspace_id: str,
    last_checked_at: datetime | None,
    last_evaluated_at: datetime | None,
    last_successful_scan_at: datetime | None,
    next_due_at: datetime | None,
    last_cluster_snapshot_json: list[dict[str, object]],
    last_saved_run_id: str | None,
    latest_saved_run_generated_at: datetime | None,
    last_notified_run_id: str | None,
    latest_meaningful_update_at: datetime | None,
    consecutive_failure_count: int,
    last_error_message: str | None,
) -> AiHotTrackerTrackingState:
    now = datetime.now(UTC)
    with session_scope() as session:
        statement = select(AiHotTrackerTrackingState).where(
            AiHotTrackerTrackingState.workspace_id == workspace_id
        )
        state = session.scalar(statement)
        if state is None:
            state = AiHotTrackerTrackingState(
                workspace_id=workspace_id,
                created_at=now,
            )

        state.last_checked_at = last_checked_at
        state.last_evaluated_at = last_evaluated_at
        state.last_successful_scan_at = last_successful_scan_at
        state.next_due_at = next_due_at
        state.last_cluster_snapshot_json = last_cluster_snapshot_json
        state.last_saved_run_id = last_saved_run_id
        state.latest_saved_run_generated_at = latest_saved_run_generated_at
        state.last_notified_run_id = last_notified_run_id
        state.latest_meaningful_update_at = latest_meaningful_update_at
        state.consecutive_failure_count = consecutive_failure_count
        state.last_error_message = last_error_message
        state.updated_at = now

        session.add(state)
        session.flush()
        session.refresh(state)
        return state
