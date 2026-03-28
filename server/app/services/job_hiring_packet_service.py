from __future__ import annotations

from copy import deepcopy
from typing import cast

from app.models.task import TASK_STATUS_DONE, Task
from app.repositories import job_hiring_packet_repository, task_repository, workspace_repository
from app.schemas.job import (
    JobAssistantResult,
    JobEvidenceStatus,
    JobFitSignal,
    JobHiringPacketActionLoop,
    JobHiringPacketEventResponse,
    JobHiringPacketLink,
    JobHiringPacketResponse,
    JobHiringPacketStatus,
    JobHiringPacketSummaryResponse,
    JobShortlistResult,
    JobTaskType,
)


class JobHiringPacketAccessError(Exception):
    pass


class JobHiringPacketValidationError(Exception):
    pass


_STATUS_ORDER: tuple[JobHiringPacketStatus, ...] = (
    "collecting_materials",
    "needs_alignment",
    "review_ready",
    "shortlist_ready",
)
_EVIDENCE_STATUSES: set[str] = {"grounded_matches", "documents_only", "no_documents"}
_FIT_SIGNALS: set[str] = {
    "grounded_match_found",
    "role_requirements_grounded",
    "insufficient_grounding",
    "no_documents_available",
}


def _normalize_optional_string(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_string_list(values: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = value.strip()
        if not item or item in seen:
            continue
        normalized.append(item)
        seen.add(item)
    return normalized


def _extract_job_result(task: Task) -> JobAssistantResult:
    if task.task_type not in {"jd_summary", "resume_match"}:
        raise JobHiringPacketValidationError("Task must be a completed Job task")
    if task.status != TASK_STATUS_DONE:
        raise JobHiringPacketValidationError("Job hiring packet source task must be completed")

    result = task.output_json.get("result")
    if not isinstance(result, dict) or result.get("module_type") != "job":
        raise JobHiringPacketValidationError("Task does not contain a structured Job result")
    return JobAssistantResult.model_validate(result)


def _derive_target_role(result: JobAssistantResult) -> str | None:
    role = _normalize_optional_string(result.input.target_role)
    if role:
        return role
    role = _normalize_optional_string(result.review_brief.role_summary)
    if role and role != "General hiring review":
        return role
    for candidate in result.comparison_candidates:
        candidate_role = _normalize_optional_string(candidate.target_role)
        if candidate_role:
            return candidate_role
    return None


def _derive_target_role_key(target_role: str | None) -> str | None:
    return target_role.casefold() if target_role else None


def _derive_packet_title(*, result: JobAssistantResult, existing_title: str | None = None) -> str:
    if existing_title:
        return existing_title
    target_role = _derive_target_role(result)
    if target_role:
        return f"{target_role} \u62db\u8058\u5de5\u4f5c\u53f0"[:255]
    return result.title[:255]


def _derive_packet_status(result: JobAssistantResult) -> JobHiringPacketStatus:
    if result.shortlist is not None:
        return "shortlist_ready"
    if result.assessment.recommended_outcome == "gather_hiring_materials":
        return "collecting_materials"
    if result.assessment.recommended_outcome in {"clarify_role_definition", "collect_more_hiring_signal"}:
        return "needs_alignment"
    return "review_ready"


def _build_packet_metadata(*, packet_id: str, event_id: str, packet_status: JobHiringPacketStatus) -> dict[str, object]:
    return {
        "job_hiring_packet": JobHiringPacketLink(
            packet_id=packet_id,
            event_id=event_id,
            packet_status=packet_status,
        ).model_dump()
    }


def _write_packet_metadata_to_task(
    *,
    task: Task,
    packet_id: str,
    event_id: str,
    packet_status: JobHiringPacketStatus,
) -> None:
    output_json = deepcopy(task.output_json)
    result = output_json.get("result")
    if not isinstance(result, dict):
        return

    metadata = result.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
        result["metadata"] = metadata
    metadata.update(_build_packet_metadata(packet_id=packet_id, event_id=event_id, packet_status=packet_status))
    task_repository.update_task_status(task.id, next_status=task.status, output_json=output_json)


def _collect_candidate_labels(result: JobAssistantResult) -> list[str]:
    labels: list[str] = []
    if result.input.candidate_label:
        labels.append(result.input.candidate_label)
    labels.extend(candidate.candidate_label for candidate in result.comparison_candidates)
    if result.shortlist is not None:
        labels.extend(entry.candidate_label for entry in result.shortlist.entries)
    return _normalize_string_list(labels)


def _merge_candidate_labels(existing_labels: list[object] | None, result: JobAssistantResult) -> list[str]:
    merged: list[str] = []
    if isinstance(existing_labels, list):
        merged.extend(item for item in existing_labels if isinstance(item, str))
    merged.extend(_collect_candidate_labels(result))
    return _normalize_string_list(merged)


def _coerce_status(value: str) -> JobHiringPacketStatus:
    if value in _STATUS_ORDER:
        return cast(JobHiringPacketStatus, value)
    raise JobHiringPacketValidationError("Job hiring packet status is invalid")


def _coerce_evidence_status(value: str | None) -> JobEvidenceStatus | None:
    if isinstance(value, str) and value in _EVIDENCE_STATUSES:
        return cast(JobEvidenceStatus, value)
    return None


def _coerce_fit_signal(value: str | None) -> JobFitSignal | None:
    if isinstance(value, str) and value in _FIT_SIGNALS:
        return cast(JobFitSignal, value)
    return None


def _build_packet_summary_response(packet) -> JobHiringPacketSummaryResponse:
    latest_result = JobAssistantResult.model_validate(packet.latest_result_json)
    latest_shortlist = (
        JobShortlistResult.model_validate(packet.latest_shortlist_json)
        if isinstance(packet.latest_shortlist_json, dict)
        else latest_result.shortlist
    )
    candidate_labels = [
        item
        for item in packet.candidate_labels_json
        if isinstance(item, str)
    ]
    return JobHiringPacketSummaryResponse(
        id=packet.id,
        workspace_id=packet.workspace_id,
        created_by=packet.created_by,
        title=packet.title,
        status=_coerce_status(packet.status),
        action_loop=_derive_packet_action_loop(
            packet_status=_coerce_status(packet.status),
            latest_task_id=packet.latest_task_id,
            latest_result=latest_result,
            latest_shortlist=latest_shortlist,
            candidate_labels=candidate_labels,
        ),
        target_role=packet.target_role,
        seniority=packet.seniority,
        latest_task_id=packet.latest_task_id,
        latest_task_type=latest_result.task_type,
        latest_summary=packet.latest_summary,
        latest_review_brief=latest_result.review_brief,
        latest_assessment=latest_result.assessment,
        latest_shortlist=latest_shortlist,
        latest_next_steps=list(latest_result.next_steps),
        latest_candidate_labels=candidate_labels,
        latest_packet_note=_derive_packet_note(latest_result=latest_result, latest_shortlist=latest_shortlist),
        latest_recommended_outcome=packet.latest_recommended_outcome,
        latest_evidence_status=_coerce_evidence_status(packet.latest_evidence_status),
        latest_fit_signal=_coerce_fit_signal(packet.latest_fit_signal),
        comparison_history_count=packet.comparison_history_count,
        event_count=packet.event_count,
        created_at=packet.created_at.isoformat(),
        updated_at=packet.updated_at.isoformat(),
    )


def _build_packet_event_response(event) -> JobHiringPacketEventResponse:
    return JobHiringPacketEventResponse(
        id=event.id,
        job_hiring_packet_id=event.job_hiring_packet_id,
        task_id=event.task_id,
        task_type=event.task_type,
        event_kind=event.event_kind,
        title=event.title,
        summary=event.summary,
        packet_status=_coerce_status(event.packet_status),
        candidate_label=event.candidate_label,
        target_role=event.target_role,
        fit_signal=_coerce_fit_signal(event.fit_signal),
        evidence_status=_coerce_evidence_status(event.evidence_status),
        recommended_outcome=event.recommended_outcome,
        comparison_task_ids=[
            item
            for item in event.comparison_task_ids_json
            if isinstance(item, str)
        ],
        shortlist_entry_count=event.shortlist_entry_count,
        created_at=event.created_at.isoformat(),
    )


def _derive_packet_note(
    *,
    latest_result: JobAssistantResult,
    latest_shortlist: JobShortlistResult | None,
) -> str | None:
    if latest_shortlist is not None and latest_shortlist.comparison_notes:
        return latest_shortlist.comparison_notes
    if latest_result.input.comparison_notes:
        return latest_result.input.comparison_notes
    rationale = _normalize_optional_string(latest_result.assessment.rationale)
    if rationale:
        return rationale
    next_step = next(
        (
            _normalize_optional_string(item)
            for item in latest_result.next_steps
            if _normalize_optional_string(item) is not None
        ),
        None,
    )
    return next_step


def _derive_packet_action_loop(
    *,
    packet_status: JobHiringPacketStatus,
    latest_task_id: str | None,
    latest_result: JobAssistantResult,
    latest_shortlist: JobShortlistResult | None,
    candidate_labels: list[str],
) -> JobHiringPacketActionLoop:
    if packet_status == "collecting_materials":
        suggested_task_type: JobTaskType = "jd_summary"
        comparison_mode = False
        status_guidance = "当前 hiring packet 还在补齐岗位材料，下一步更适合先刷新岗位摘要，再继续候选人评审。"
    elif packet_status == "needs_alignment":
        suggested_task_type = "jd_summary"
        comparison_mode = False
        status_guidance = "当前 hiring packet 还需要对齐岗位要求，下一步更适合先更新岗位定义和 must-have 技能。"
    elif latest_shortlist is not None or len(candidate_labels) >= 2:
        suggested_task_type = "resume_match"
        comparison_mode = True
        status_guidance = "当前 hiring packet 已有可比较的候选池，下一步可以直接刷新短名单，或在补充新候选人后重新比较。"
    else:
        suggested_task_type = "resume_match"
        comparison_mode = False
        status_guidance = "当前 hiring packet 还在积累候选人评审，下一步更适合继续补一位候选人的 grounded 评审。"

    suggested_note_prompt = _derive_packet_note(
        latest_result=latest_result,
        latest_shortlist=latest_shortlist,
    )

    return JobHiringPacketActionLoop(
        can_continue=isinstance(latest_task_id, str) and bool(latest_task_id),
        suggested_task_type=suggested_task_type,
        comparison_mode=comparison_mode,
        status_guidance=status_guidance,
        suggested_note_prompt=suggested_note_prompt,
    )


def _build_packet_response(packet_id: str) -> JobHiringPacketResponse:
    packet = job_hiring_packet_repository.get_job_hiring_packet(packet_id)
    if packet is None:
        raise JobHiringPacketValidationError("Job hiring packet not found")
    events = job_hiring_packet_repository.list_job_hiring_packet_events(packet_id)
    summary = _build_packet_summary_response(packet)
    return JobHiringPacketResponse(
        **summary.model_dump(),
        events=[_build_packet_event_response(event) for event in events],
    )


def sync_job_hiring_packet_from_task(*, task: Task, result_json: dict[str, object]) -> dict[str, object]:
    result = JobAssistantResult.model_validate(result_json)

    existing_event = job_hiring_packet_repository.get_job_hiring_packet_event_by_task_id(task.id)
    if existing_event is not None:
        return _build_packet_metadata(
            packet_id=existing_event.job_hiring_packet_id,
            event_id=existing_event.id,
            packet_status=_coerce_status(existing_event.packet_status),
        )

    packet_status = _derive_packet_status(result)
    target_role = _derive_target_role(result)
    target_role_key = _derive_target_role_key(target_role)
    linked_packet = None
    if target_role_key is not None:
        linked_packet = job_hiring_packet_repository.get_workspace_job_hiring_packet_by_role_key(
            task.workspace_id,
            target_role_key,
        )

    candidate_labels = _merge_candidate_labels(
        linked_packet.candidate_labels_json if linked_packet is not None else None,
        result,
    )
    comparison_history_count = (linked_packet.comparison_history_count if linked_packet is not None else 0) + (
        1 if result.shortlist is not None else 0
    )
    event_kind = "shortlist_refresh" if result.shortlist is not None else "candidate_review"
    latest_shortlist_json = result.shortlist.model_dump(exclude_none=True) if result.shortlist is not None else None

    if linked_packet is None:
        linked_packet = job_hiring_packet_repository.create_job_hiring_packet(
            workspace_id=task.workspace_id,
            created_by=task.created_by,
            title=_derive_packet_title(result=result),
            status=packet_status,
            target_role=target_role,
            target_role_key=target_role_key,
            seniority=result.input.seniority,
            latest_task_id=task.id,
            latest_task_type=task.task_type,
            latest_input_json=deepcopy(task.input_json),
            latest_result_json=deepcopy(result_json),
            latest_summary=result.summary,
            latest_recommended_outcome=result.assessment.recommended_outcome,
            latest_evidence_status=result.assessment.evidence_status,
            latest_fit_signal=result.assessment.fit_signal,
            latest_shortlist_json=latest_shortlist_json,
            latest_next_steps_json=list(result.next_steps),
            candidate_labels_json=candidate_labels,
            comparison_history_count=comparison_history_count,
        )
        current_event_count = 1
    else:
        current_event_count = linked_packet.event_count + 1
        job_hiring_packet_repository.update_job_hiring_packet_snapshot(
            linked_packet.id,
            title=_derive_packet_title(result=result, existing_title=linked_packet.title),
            status=packet_status,
            target_role=target_role,
            target_role_key=target_role_key,
            seniority=result.input.seniority,
            latest_task_id=task.id,
            latest_task_type=task.task_type,
            latest_input_json=deepcopy(task.input_json),
            latest_result_json=deepcopy(result_json),
            latest_summary=result.summary,
            latest_recommended_outcome=result.assessment.recommended_outcome,
            latest_evidence_status=result.assessment.evidence_status,
            latest_fit_signal=result.assessment.fit_signal,
            latest_shortlist_json=latest_shortlist_json,
            latest_next_steps_json=list(result.next_steps),
            candidate_labels_json=candidate_labels,
            comparison_history_count=comparison_history_count,
            event_count=current_event_count,
        )

    event = job_hiring_packet_repository.create_job_hiring_packet_event(
        job_hiring_packet_id=linked_packet.id,
        task_id=task.id,
        task_type=task.task_type,
        event_kind=event_kind,
        title=result.title,
        summary=result.summary,
        packet_status=packet_status,
        candidate_label=result.input.candidate_label,
        target_role=target_role,
        fit_signal=result.assessment.fit_signal,
        evidence_status=result.assessment.evidence_status,
        recommended_outcome=result.assessment.recommended_outcome,
        comparison_task_ids_json=list(result.input.comparison_task_ids),
        shortlist_entry_count=len(result.shortlist.entries) if result.shortlist is not None else 0,
        created_at=task.updated_at,
    )
    _write_packet_metadata_to_task(
        task=task,
        packet_id=linked_packet.id,
        event_id=event.id,
        packet_status=packet_status,
    )
    return _build_packet_metadata(
        packet_id=linked_packet.id,
        event_id=event.id,
        packet_status=packet_status,
    )


def list_workspace_job_hiring_packets(*, workspace_id: str, user_id: str) -> list[JobHiringPacketSummaryResponse]:
    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        raise JobHiringPacketAccessError("Workspace not found")

    packets = job_hiring_packet_repository.list_workspace_job_hiring_packets(workspace_id, user_id)
    return [_build_packet_summary_response(packet) for packet in packets]


def get_job_hiring_packet(*, packet_id: str, user_id: str) -> JobHiringPacketResponse | None:
    packet = job_hiring_packet_repository.get_job_hiring_packet_for_user(packet_id, user_id)
    if packet is None:
        return None
    return _build_packet_response(packet.id)
