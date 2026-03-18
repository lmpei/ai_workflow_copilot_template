from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime

CONTROL_ACTION_CANCEL = "cancel"
CONTROL_ACTION_RETRY = "retry"

CONTROL_STATE_CANCEL_REQUESTED = "cancel_requested"
CONTROL_STATE_CANCELLED = "cancelled"
CONTROL_STATE_RETRY_CREATED = "retry_created"
CONTROL_STATE_RETRY_ATTEMPT = "retry_attempt"


def clone_control_json(control_json: dict[str, object] | None) -> dict[str, object]:
    if isinstance(control_json, dict):
        return deepcopy(control_json)
    return {}


def derive_recovery_state(*, status: str, control_json: dict[str, object] | None) -> str:
    if isinstance(control_json, dict):
        control_state = control_json.get("state")
        if isinstance(control_state, str) and control_state:
            return control_state

    if status == "failed":
        return "retryable_failed"
    return status


def is_cancel_requested(control_json: dict[str, object] | None) -> bool:
    if not isinstance(control_json, dict):
        return False
    return (
        control_json.get("last_action") == CONTROL_ACTION_CANCEL
        and control_json.get("state") == CONTROL_STATE_CANCEL_REQUESTED
    )


def build_cancel_requested_control(
    *,
    current_control_json: dict[str, object] | None,
    user_id: str,
    reason: str | None = None,
    extra_json: dict[str, object] | None = None,
) -> dict[str, object]:
    control_json = clone_control_json(current_control_json)
    requested_at = datetime.now(UTC).isoformat()
    if (
        control_json.get("last_action") == CONTROL_ACTION_CANCEL
        and control_json.get("state") in {CONTROL_STATE_CANCEL_REQUESTED, CONTROL_STATE_CANCELLED}
    ):
        previous_requested_at = control_json.get("requested_at")
        if isinstance(previous_requested_at, str) and previous_requested_at:
            requested_at = previous_requested_at

    control_json.update(
        {
            "last_action": CONTROL_ACTION_CANCEL,
            "state": CONTROL_STATE_CANCEL_REQUESTED,
            "requested_by": user_id,
            "requested_at": requested_at,
        }
    )
    control_json.pop("applied_at", None)
    control_json.pop("applied_by", None)
    if reason:
        control_json["reason"] = reason
    if extra_json:
        control_json.update(extra_json)
    return control_json


def build_cancelled_control(
    *,
    current_control_json: dict[str, object] | None,
    user_id: str,
    reason: str | None = None,
    extra_json: dict[str, object] | None = None,
) -> dict[str, object]:
    control_json = clone_control_json(current_control_json)
    requested_at = datetime.now(UTC).isoformat()
    requested_by = user_id
    if (
        control_json.get("last_action") == CONTROL_ACTION_CANCEL
        and control_json.get("state") in {CONTROL_STATE_CANCEL_REQUESTED, CONTROL_STATE_CANCELLED}
    ):
        previous_requested_at = control_json.get("requested_at")
        if isinstance(previous_requested_at, str) and previous_requested_at:
            requested_at = previous_requested_at

        previous_requested_by = control_json.get("requested_by")
        if isinstance(previous_requested_by, str) and previous_requested_by:
            requested_by = previous_requested_by

    control_json.update(
        {
            "last_action": CONTROL_ACTION_CANCEL,
            "state": CONTROL_STATE_CANCELLED,
            "requested_by": requested_by,
            "requested_at": requested_at,
            "applied_by": user_id,
            "applied_at": datetime.now(UTC).isoformat(),
        }
    )
    if reason:
        control_json["reason"] = reason
    if extra_json:
        control_json.update(extra_json)
    return control_json


def build_retry_created_control(
    *,
    current_control_json: dict[str, object] | None,
    user_id: str,
    target_id_key: str,
    target_id: str,
    reason: str | None = None,
    extra_json: dict[str, object] | None = None,
) -> dict[str, object]:
    requested_at = datetime.now(UTC).isoformat()
    control_json = clone_control_json(current_control_json)
    control_json.update(
        {
            "last_action": CONTROL_ACTION_RETRY,
            "state": CONTROL_STATE_RETRY_CREATED,
            "requested_by": user_id,
            "requested_at": requested_at,
            "applied_by": user_id,
            "applied_at": requested_at,
            target_id_key: target_id,
        }
    )
    if reason:
        control_json["reason"] = reason
    if extra_json:
        control_json.update(extra_json)
    return control_json


def build_retry_attempt_control(
    *,
    user_id: str,
    source_id_key: str,
    source_id: str,
    reason: str | None = None,
    extra_json: dict[str, object] | None = None,
) -> dict[str, object]:
    requested_at = datetime.now(UTC).isoformat()
    control_json: dict[str, object] = {
        "last_action": CONTROL_ACTION_RETRY,
        "state": CONTROL_STATE_RETRY_ATTEMPT,
        "requested_by": user_id,
        "requested_at": requested_at,
        "applied_by": user_id,
        "applied_at": requested_at,
        source_id_key: source_id,
    }
    if reason:
        control_json["reason"] = reason
    if extra_json:
        control_json.update(extra_json)
    return control_json
