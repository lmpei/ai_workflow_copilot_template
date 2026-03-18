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
