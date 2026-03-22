from app.core import runtime_control


def test_cancel_request_overrides_retry_attempt_request_metadata() -> None:
    retry_control = runtime_control.build_retry_attempt_control(
        user_id="retry-user",
        source_id_key="source_task_id",
        source_id="task-1",
        reason="Retry after timeout.",
    )
    retry_control["requested_at"] = "2026-03-18T00:00:00+00:00"

    cancel_requested = runtime_control.build_cancel_requested_control(
        current_control_json=retry_control,
        user_id="cancel-user",
        reason="Operator stopped the retry.",
    )

    assert cancel_requested["last_action"] == runtime_control.CONTROL_ACTION_CANCEL
    assert cancel_requested["state"] == runtime_control.CONTROL_STATE_CANCEL_REQUESTED
    assert cancel_requested["requested_by"] == "cancel-user"
    assert cancel_requested["requested_at"] != retry_control["requested_at"]
    assert cancel_requested["history"][-1]["event"] == "cancel_requested"


def test_cancelled_control_preserves_existing_cancel_request_metadata() -> None:
    cancel_requested = runtime_control.build_cancel_requested_control(
        current_control_json={},
        user_id="cancel-user",
        reason="Operator requested cancellation.",
    )

    cancelled = runtime_control.build_cancelled_control(
        current_control_json=cancel_requested,
        user_id="worker-user",
        reason="Operator requested cancellation.",
    )

    assert cancelled["last_action"] == runtime_control.CONTROL_ACTION_CANCEL
    assert cancelled["state"] == runtime_control.CONTROL_STATE_CANCELLED
    assert cancelled["requested_by"] == cancel_requested["requested_by"]
    assert cancelled["requested_at"] == cancel_requested["requested_at"]
    assert cancelled["applied_by"] == "worker-user"
    assert cancelled["history"][-1]["event"] == "cancelled"


def test_build_recovery_detail_exposes_linked_retry_history() -> None:
    original_control = runtime_control.build_retry_created_control(
        current_control_json={},
        user_id="operator-1",
        target_id_key="target_task_id",
        target_id="task-2",
        reason="Retry after transient outage.",
    )

    detail = runtime_control.build_recovery_detail(status="failed", control_json=original_control)

    assert detail["state"] == runtime_control.CONTROL_STATE_RETRY_CREATED
    assert detail["last_action"] == runtime_control.CONTROL_ACTION_RETRY
    assert detail["target_task_id"] == "task-2"
    assert detail["history"][0]["event"] == "retry_created"
    assert detail["history"][0]["metadata"]["target_task_id"] == "task-2"


def test_resolve_cancel_transition_uses_shared_pending_and_running_rules() -> None:
    pending_transition = runtime_control.resolve_cancel_transition(
        current_status="pending",
        current_control_json={},
        user_id="operator-1",
        reason="Stop before execution.",
        cancelled_error_message="Task cancelled by operator",
    )
    running_transition = runtime_control.resolve_cancel_transition(
        current_status="running",
        current_control_json={},
        user_id="operator-1",
        reason="Stop while running.",
        cancelled_error_message="Task cancelled by operator",
    )

    assert pending_transition.next_status == "failed"
    assert pending_transition.error_message == "Task cancelled by operator"
    assert pending_transition.control_json["state"] == runtime_control.CONTROL_STATE_CANCELLED
    assert running_transition.next_status == "running"
    assert running_transition.error_message is None
    assert running_transition.control_json["state"] == runtime_control.CONTROL_STATE_CANCEL_REQUESTED


def test_build_cancelled_control_from_request_reuses_requested_metadata() -> None:
    cancel_requested = runtime_control.build_cancel_requested_control(
        current_control_json={},
        user_id="operator-1",
        reason="Cancel this work.",
    )

    cancelled = runtime_control.build_cancelled_control_from_request(
        current_status="running",
        current_control_json=cancel_requested,
        fallback_user_id="worker-1",
    )

    assert cancelled["requested_by"] == "operator-1"
    assert cancelled["reason"] == "Cancel this work."
    assert cancelled["state"] == runtime_control.CONTROL_STATE_CANCELLED
    assert cancelled["cancelled_from_status"] == "running"
