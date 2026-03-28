from __future__ import annotations

from copy import deepcopy
from typing import cast

from app.models.task import TASK_STATUS_DONE, Task
from app.repositories import support_case_repository, task_repository, workspace_repository
from app.schemas.support import (
    SupportCaseActionLoop,
    SupportCaseEventResponse,
    SupportCaseLink,
    SupportCaseResponse,
    SupportCaseStatus,
    SupportCaseSummaryResponse,
    SupportCopilotResult,
    SupportTaskType,
)


class SupportCaseAccessError(Exception):
    pass


class SupportCaseValidationError(Exception):
    pass


def _extract_support_result(task: Task) -> SupportCopilotResult:
    if task.task_type not in {"ticket_summary", "reply_draft"}:
        raise SupportCaseValidationError("任务必须是已完成的 Support 任务")
    if task.status != TASK_STATUS_DONE:
        raise SupportCaseValidationError("Support case 来源任务必须已经完成")

    result = task.output_json.get("result")
    if not isinstance(result, dict) or result.get("module_type") != "support":
        raise SupportCaseValidationError("任务中不包含结构化的 Support 结果")
    return SupportCopilotResult.model_validate(result)


def _derive_case_title(*, result: SupportCopilotResult, existing_title: str | None = None) -> str:
    if existing_title:
        return existing_title
    issue_summary = result.case_brief.issue_summary.strip()
    if issue_summary:
        return issue_summary[:255]
    return result.title[:255]


def _derive_case_status(*, result: SupportCopilotResult) -> SupportCaseStatus:
    if result.triage.should_escalate:
        return "escalated"
    if result.task_type == "reply_draft" and result.triage.evidence_status == "grounded_matches":
        return "ready_for_reply"
    if result.open_questions:
        return "needs_customer_input"
    return "open"


def _build_case_metadata(*, case_id: str, event_id: str, case_status: SupportCaseStatus) -> dict[str, object]:
    return {
        "support_case": SupportCaseLink(
            case_id=case_id,
            event_id=event_id,
            case_status=case_status,
        ).model_dump()
    }


def _write_case_metadata_to_task(
    *,
    task: Task,
    case_id: str,
    event_id: str,
    case_status: SupportCaseStatus,
) -> None:
    output_json = deepcopy(task.output_json)
    result = output_json.get("result")
    if not isinstance(result, dict):
        return

    metadata = result.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
        result["metadata"] = metadata
    metadata.update(_build_case_metadata(case_id=case_id, event_id=event_id, case_status=case_status))
    task_repository.update_task_status(task.id, next_status=task.status, output_json=output_json)


def _derive_case_action_loop(
    *,
    case_status: SupportCaseStatus,
    latest_task_id: str | None,
    latest_result: SupportCopilotResult,
) -> SupportCaseActionLoop:
    suggested_task_type: SupportTaskType
    if case_status == "ready_for_reply":
        suggested_task_type = "reply_draft"
        status_guidance = "当前 case 已经具备回复条件，下一步更适合继续生成或刷新回复草稿。"
    elif case_status == "needs_customer_input":
        suggested_task_type = "ticket_summary"
        status_guidance = "当前 case 还缺客户补充信息，下一步应记录新反馈并刷新 case 摘要。"
    elif case_status == "escalated":
        suggested_task_type = "ticket_summary"
        status_guidance = "当前 case 已进入升级处理，下一步应记录人工跟进结果，再决定是否需要新的回复草稿。"
    else:
        suggested_task_type = "ticket_summary"
        status_guidance = "当前 case 仍在处理中，下一步应继续核实信息并推进分诊。"

    suggested_follow_up_prompt: str | None = None
    if case_status == "needs_customer_input" and latest_result.open_questions:
        suggested_follow_up_prompt = latest_result.open_questions[0]
    elif latest_result.next_steps:
        suggested_follow_up_prompt = latest_result.next_steps[0]
    elif latest_result.open_questions:
        suggested_follow_up_prompt = latest_result.open_questions[0]

    return SupportCaseActionLoop(
        can_continue=isinstance(latest_task_id, str) and bool(latest_task_id),
        continue_from_task_id=latest_task_id,
        suggested_task_type=suggested_task_type,
        status_guidance=status_guidance,
        suggested_follow_up_prompt=suggested_follow_up_prompt,
    )


def _build_case_summary_response(case) -> SupportCaseSummaryResponse:
    latest_result = SupportCopilotResult.model_validate(case.latest_result_json)
    return SupportCaseSummaryResponse(
        id=case.id,
        workspace_id=case.workspace_id,
        created_by=case.created_by,
        title=case.title,
        status=cast(SupportCaseStatus, case.status),
        action_loop=_derive_case_action_loop(
            case_status=cast(SupportCaseStatus, case.status),
            latest_task_id=case.latest_task_id,
            latest_result=latest_result,
        ),
        latest_task_id=case.latest_task_id,
        latest_task_type=latest_result.task_type,
        latest_summary=case.latest_summary,
        latest_case_brief=latest_result.case_brief,
        latest_triage=latest_result.triage,
        latest_escalation_packet=latest_result.escalation_packet,
        latest_open_questions=latest_result.open_questions,
        latest_next_steps=latest_result.next_steps,
        latest_recommended_owner=case.latest_recommended_owner,
        latest_evidence_status=case.latest_evidence_status,
        event_count=case.event_count,
        created_at=case.created_at,
        updated_at=case.updated_at,
    )


def _build_case_event_response(event) -> SupportCaseEventResponse:
    return SupportCaseEventResponse(
        id=event.id,
        support_case_id=event.support_case_id,
        task_id=event.task_id,
        task_type=event.task_type,
        event_kind=event.event_kind,
        title=event.title,
        summary=event.summary,
        case_status=cast(SupportCaseStatus, event.case_status),
        recommended_owner=event.recommended_owner,
        evidence_status=event.evidence_status,
        should_escalate=event.should_escalate,
        needs_manual_review=event.needs_manual_review,
        follow_up_notes=event.follow_up_notes,
        created_at=event.created_at,
    )


def _build_case_response(case_id: str) -> SupportCaseResponse:
    case = support_case_repository.get_support_case(case_id)
    if case is None:
        raise SupportCaseValidationError("未找到 Support case")
    events = support_case_repository.list_support_case_events(case_id)
    summary = _build_case_summary_response(case)
    return SupportCaseResponse(
        **summary.model_dump(),
        events=[_build_case_event_response(event) for event in events],
    )


def _resolve_linked_case(task: Task):
    parent_task_id = task.input_json.get("parent_task_id")
    if not isinstance(parent_task_id, str) or not parent_task_id:
        return None, 0

    parent_event = support_case_repository.get_support_case_event_by_task_id(parent_task_id)
    if parent_event is None:
        return None, 0
    parent_case = support_case_repository.get_support_case(parent_event.support_case_id)
    if parent_case is None:
        return None, 0
    return parent_case, parent_case.event_count


def sync_support_case_from_task(*, task: Task, result_json: dict[str, object]) -> dict[str, object]:
    result = SupportCopilotResult.model_validate(result_json)

    existing_event = support_case_repository.get_support_case_event_by_task_id(task.id)
    if existing_event is not None:
        return _build_case_metadata(
            case_id=existing_event.support_case_id,
            event_id=existing_event.id,
            case_status=cast(SupportCaseStatus, existing_event.case_status),
        )

    linked_case, current_event_count = _resolve_linked_case(task)
    case_status = _derive_case_status(result=result)
    event_kind = "follow_up" if result.lineage is not None else "case_created"
    follow_up_notes = result.lineage.follow_up_notes if result.lineage is not None else None

    if linked_case is None:
        linked_case = support_case_repository.create_support_case(
            workspace_id=task.workspace_id,
            created_by=task.created_by,
            title=_derive_case_title(result=result),
            status=case_status,
            latest_task_id=task.id,
            latest_task_type=task.task_type,
            latest_input_json=deepcopy(task.input_json),
            latest_result_json=deepcopy(result_json),
            latest_summary=result.summary,
            latest_recommended_owner=result.triage.recommended_owner,
            latest_evidence_status=result.triage.evidence_status,
        )
        current_event_count = 1
    else:
        current_event_count += 1
        support_case_repository.update_support_case_snapshot(
            linked_case.id,
            title=_derive_case_title(result=result, existing_title=linked_case.title),
            status=case_status,
            latest_task_id=task.id,
            latest_task_type=task.task_type,
            latest_input_json=deepcopy(task.input_json),
            latest_result_json=deepcopy(result_json),
            latest_summary=result.summary,
            latest_recommended_owner=result.triage.recommended_owner,
            latest_evidence_status=result.triage.evidence_status,
            event_count=current_event_count,
        )

    event = support_case_repository.create_support_case_event(
        support_case_id=linked_case.id,
        task_id=task.id,
        task_type=task.task_type,
        event_kind=event_kind,
        title=result.title,
        summary=result.summary,
        case_status=case_status,
        recommended_owner=result.triage.recommended_owner,
        evidence_status=result.triage.evidence_status,
        should_escalate=result.triage.should_escalate,
        needs_manual_review=result.triage.needs_manual_review,
        follow_up_notes=follow_up_notes,
        created_at=task.updated_at,
    )
    _write_case_metadata_to_task(task=task, case_id=linked_case.id, event_id=event.id, case_status=case_status)
    return _build_case_metadata(case_id=linked_case.id, event_id=event.id, case_status=case_status)


def list_workspace_support_cases(*, workspace_id: str, user_id: str) -> list[SupportCaseSummaryResponse]:
    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        raise SupportCaseAccessError("未找到工作区")

    cases = support_case_repository.list_workspace_support_cases(workspace_id, user_id)
    return [_build_case_summary_response(case) for case in cases]


def get_support_case(*, case_id: str, user_id: str) -> SupportCaseResponse | None:
    case = support_case_repository.get_support_case_for_user(case_id, user_id)
    if case is None:
        return None
    return _build_case_response(case.id)

