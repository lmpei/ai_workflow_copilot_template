"""Shared runtime-control helpers for task and eval recovery semantics.

This module owns the persisted control-state shape, transition builders, and
operator-facing recovery detail. Service layers should derive cancel/retry
behavior here instead of hand-assembling control_json mutations.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime

CONTROL_ACTION_CANCEL = "cancel"
CONTROL_ACTION_RETRY = "retry"

CONTROL_STATE_CANCEL_REQUESTED = "cancel_requested"
CONTROL_STATE_CANCELLED = "cancelled"
CONTROL_STATE_RETRY_CREATED = "retry_created"
CONTROL_STATE_RETRY_ATTEMPT = "retry_attempt"


@dataclass(frozen=True, slots=True)
class RuntimeControlTransition:
    next_status: str
    control_json: dict[str, object]
    error_message: str | None = None


def clone_control_json(control_json: dict[str, object] | None) -> dict[str, object]:
    if isinstance(control_json, dict):
        return deepcopy(control_json)
    return {}


def _coerce_history(control_json: dict[str, object] | None) -> list[dict[str, object]]:
    if not isinstance(control_json, dict):
        return []

    raw_history = control_json.get("history")
    if not isinstance(raw_history, list):
        return []

    history: list[dict[str, object]] = []
    for item in raw_history:
        if not isinstance(item, dict):
            continue

        event = item.get("event")
        at = item.get("at")
        if not isinstance(event, str) or not event or not isinstance(at, str) or not at:
            continue

        normalized_item: dict[str, object] = {
            "event": event,
            "at": at,
        }
        state = item.get("state")
        if isinstance(state, str) and state:
            normalized_item["state"] = state
        actor_id = item.get("by")
        if isinstance(actor_id, str) and actor_id:
            normalized_item["by"] = actor_id
        reason = item.get("reason")
        if isinstance(reason, str) and reason:
            normalized_item["reason"] = reason
        metadata = item.get("metadata")
        if isinstance(metadata, dict) and metadata:
            normalized_item["metadata"] = deepcopy(metadata)
        history.append(normalized_item)

    return history


def _append_history_entry(
    control_json: dict[str, object],
    *,
    event: str,
    state: str,
    actor_id: str,
    timestamp: str,
    reason: str | None = None,
    metadata: dict[str, object] | None = None,
) -> dict[str, object]:
    history = _coerce_history(control_json)
    entry: dict[str, object] = {
        "event": event,
        "state": state,
        "at": timestamp,
        "by": actor_id,
    }
    if reason:
        entry["reason"] = reason
    if metadata:
        entry["metadata"] = deepcopy(metadata)
    history.append(entry)
    control_json["history"] = history
    return control_json


def derive_recovery_state(*, status: str, control_json: dict[str, object] | None) -> str:
    if isinstance(control_json, dict):
        control_state = control_json.get("state")
        if isinstance(control_state, str) and control_state:
            return control_state

    if status == "failed":
        return "retryable_failed"
    return status


def get_control_state(control_json: dict[str, object] | None) -> str | None:
    if not isinstance(control_json, dict):
        return None

    control_state = control_json.get("state")
    if isinstance(control_state, str) and control_state:
        return control_state
    return None


def build_recovery_detail(*, status: str, control_json: dict[str, object] | None) -> dict[str, object]:
    detail: dict[str, object] = {
        "state": derive_recovery_state(status=status, control_json=control_json),
        "history": _coerce_history(control_json),
        "metadata": {},
    }
    if not isinstance(control_json, dict):
        return detail

    for key in ("last_action", "reason", "requested_by", "requested_at", "applied_by", "applied_at"):
        value = control_json.get(key)
        if isinstance(value, str) and value:
            detail[key] = value

    for key in ("source_task_id", "target_task_id", "source_eval_run_id", "target_eval_run_id"):
        value = control_json.get(key)
        if isinstance(value, str) and value:
            detail[key] = value

    metadata: dict[str, object] = {}
    for key in (
        "cancel_requested_from_status",
        "cancelled_from_status",
        "retry_enqueue_failed",
    ):
        value = control_json.get(key)
        if value is not None:
            metadata[key] = deepcopy(value)
    if metadata:
        detail["metadata"] = metadata

    return detail


def is_cancel_requested(control_json: dict[str, object] | None) -> bool:
    if not isinstance(control_json, dict):
        return False
    return (
        control_json.get("last_action") == CONTROL_ACTION_CANCEL
        and control_json.get("state") == CONTROL_STATE_CANCEL_REQUESTED
    )


def is_cancel_recorded(control_json: dict[str, object] | None) -> bool:
    return get_control_state(control_json) in {
        CONTROL_STATE_CANCEL_REQUESTED,
        CONTROL_STATE_CANCELLED,
    }


def get_linked_retry_target_id(
    control_json: dict[str, object] | None,
    *,
    target_id_key: str,
) -> str | None:
    if not isinstance(control_json, dict):
        return None

    target_id = control_json.get(target_id_key)
    if isinstance(target_id, str) and target_id:
        return target_id
    return None


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
    return _append_history_entry(
        control_json,
        event="cancel_requested",
        state=CONTROL_STATE_CANCEL_REQUESTED,
        actor_id=user_id,
        timestamp=requested_at,
        reason=reason,
        metadata=extra_json,
    )


def resolve_cancel_transition(
    *,
    current_status: str,
    current_control_json: dict[str, object] | None,
    user_id: str,
    reason: str | None,
    cancelled_error_message: str,
) -> RuntimeControlTransition:
    """Resolve the operator-facing cancel transition for pending or running work."""
    if current_status == "pending":
        return RuntimeControlTransition(
            next_status="failed",
            control_json=build_cancelled_control(
                current_control_json=current_control_json,
                user_id=user_id,
                reason=reason,
                extra_json={"cancelled_from_status": "pending"},
            ),
            error_message=cancelled_error_message,
        )

    if current_status == "running":
        return RuntimeControlTransition(
            next_status="running",
            control_json=build_cancel_requested_control(
                current_control_json=current_control_json,
                user_id=user_id,
                reason=reason,
                extra_json={"cancel_requested_from_status": "running"},
            ),
        )

    raise ValueError("Only pending or running runtime items can be cancelled")


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

    applied_at = datetime.now(UTC).isoformat()
    control_json.update(
        {
            "last_action": CONTROL_ACTION_CANCEL,
            "state": CONTROL_STATE_CANCELLED,
            "requested_by": requested_by,
            "requested_at": requested_at,
            "applied_by": user_id,
            "applied_at": applied_at,
        }
    )
    if reason:
        control_json["reason"] = reason
    if extra_json:
        control_json.update(extra_json)
    return _append_history_entry(
        control_json,
        event="cancelled",
        state=CONTROL_STATE_CANCELLED,
        actor_id=user_id,
        timestamp=applied_at,
        reason=reason,
        metadata=extra_json,
    )


def build_cancelled_control_from_request(
    *,
    current_status: str,
    current_control_json: dict[str, object] | None,
    fallback_user_id: str,
) -> dict[str, object]:
    """Apply a previously recorded cancel request at a worker-safe boundary."""
    control_json = current_control_json if isinstance(current_control_json, dict) else {}
    requested_by = control_json.get("requested_by")
    reason = control_json.get("reason")

    return build_cancelled_control(
        current_control_json=current_control_json,
        user_id=str(requested_by) if isinstance(requested_by, str) and requested_by else fallback_user_id,
        reason=str(reason) if isinstance(reason, str) and reason else None,
        extra_json={"cancelled_from_status": current_status},
    )


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

    entry_metadata: dict[str, object] = {target_id_key: target_id}
    if extra_json:
        entry_metadata.update(extra_json)
    return _append_history_entry(
        control_json,
        event="retry_created",
        state=CONTROL_STATE_RETRY_CREATED,
        actor_id=user_id,
        timestamp=requested_at,
        reason=reason,
        metadata=entry_metadata,
    )


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

    entry_metadata: dict[str, object] = {source_id_key: source_id}
    if extra_json:
        entry_metadata.update(extra_json)
    return _append_history_entry(
        control_json,
        event="retry_attempt",
        state=CONTROL_STATE_RETRY_ATTEMPT,
        actor_id=user_id,
        timestamp=requested_at,
        reason=reason,
        metadata=entry_metadata,
    )
