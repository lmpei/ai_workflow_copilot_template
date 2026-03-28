from collections.abc import Sequence
from typing import cast

from pydantic import ValidationError

from app.repositories import task_repository
from app.schemas.scenario import (
    MODULE_TYPE_SUPPORT,
    ScenarioEvidenceItem,
    get_scenario_task_module_type,
    get_supported_scenario_task_types,
)
from app.schemas.support import (
    SupportArtifacts,
    SupportCaseBrief,
    SupportCaseLineage,
    SupportCopilotResult,
    SupportEscalationPacket,
    SupportEvidenceStatus,
    SupportFinding,
    SupportReplyDraft,
    SupportSeverity,
    SupportTaskInput,
    SupportTaskType,
    SupportTriageDecision,
)
from app.schemas.tool import SearchDocumentMatch, ToolDocumentSummary

_SUPPORT_TASK_TITLES = {
    "ticket_summary": "Support Ticket Summary",
    "reply_draft": "Grounded Reply Draft",
}
_SUPPORT_EVIDENCE_STATUSES = {"grounded_matches", "documents_only", "no_documents"}
_SUPPORT_SEVERITIES = {"low", "medium", "high", "critical"}


class SupportCopilotContractError(ValueError):
    pass


def validate_support_task_contract(*, workspace_module_type: str, task_type: str) -> None:
    supported_for_module = set(get_supported_scenario_task_types(workspace_module_type))
    if task_type not in supported_for_module:
        raise SupportCopilotContractError(
            f"Task type {task_type} is not supported for workspace module {workspace_module_type}",
        )
    if get_scenario_task_module_type(task_type) != MODULE_TYPE_SUPPORT:
        raise SupportCopilotContractError(
            f"Support Copilot does not support task type: {task_type}",
        )
    if workspace_module_type != MODULE_TYPE_SUPPORT:
        raise SupportCopilotContractError(
            f"Support Copilot requires workspace module {MODULE_TYPE_SUPPORT}",
        )


def _normalize_optional_string(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_string_list(values: Sequence[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = value.strip()
        if not item or item in seen:
            continue
        normalized.append(item)
        seen.add(item)
    return normalized


def _coerce_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return _normalize_string_list([item for item in value if isinstance(item, str)])


def _coerce_support_severity(value: object) -> SupportSeverity | None:
    if isinstance(value, str) and value in _SUPPORT_SEVERITIES:
        return cast(SupportSeverity, value)
    return None


def _coerce_support_evidence_status(value: object) -> SupportEvidenceStatus | None:
    if isinstance(value, str) and value in _SUPPORT_EVIDENCE_STATUSES:
        return cast(SupportEvidenceStatus, value)
    return None


def normalize_support_task_input(input_json: dict[str, object] | None) -> dict[str, object]:
    raw_input = input_json or {}
    if raw_input.get("customer_issue") is None and isinstance(raw_input.get("goal"), str):
        raise SupportCopilotContractError(
            "Support task input must use customer_issue instead of goal",
        )

    payload_input = {
        "customer_issue": raw_input.get("customer_issue"),
        "product_area": raw_input.get("product_area"),
        "severity": raw_input.get("severity"),
        "desired_outcome": raw_input.get("desired_outcome"),
        "reproduction_steps": raw_input.get("reproduction_steps", []),
        "parent_task_id": raw_input.get("parent_task_id"),
        "follow_up_notes": raw_input.get("follow_up_notes"),
    }
    try:
        payload = SupportTaskInput.model_validate(payload_input)
    except ValidationError as error:
        raise SupportCopilotContractError("Support 任务输入无效") from error

    normalized_payload: dict[str, object] = {}
    normalized_issue = _normalize_optional_string(payload.customer_issue)
    if normalized_issue:
        normalized_payload["customer_issue"] = normalized_issue

    normalized_product_area = _normalize_optional_string(payload.product_area)
    if normalized_product_area:
        normalized_payload["product_area"] = normalized_product_area

    if payload.severity is not None:
        normalized_payload["severity"] = payload.severity

    normalized_outcome = _normalize_optional_string(payload.desired_outcome)
    if normalized_outcome:
        normalized_payload["desired_outcome"] = normalized_outcome

    normalized_steps = _normalize_string_list(payload.reproduction_steps)
    if normalized_steps:
        normalized_payload["reproduction_steps"] = normalized_steps

    normalized_parent_task_id = _normalize_optional_string(payload.parent_task_id)
    if normalized_parent_task_id:
        normalized_payload["parent_task_id"] = normalized_parent_task_id

    normalized_follow_up_notes = _normalize_optional_string(payload.follow_up_notes)
    if normalized_follow_up_notes:
        normalized_payload["follow_up_notes"] = normalized_follow_up_notes

    return normalized_payload


def resolve_support_task_input(input_json: dict[str, object] | None) -> SupportTaskInput:
    try:
        return SupportTaskInput.model_validate(normalize_support_task_input(input_json))
    except ValidationError as error:
        raise SupportCopilotContractError("Support 任务输入无效") from error


def resolve_support_task_lineage(
    *,
    workspace_id: str,
    support_input: SupportTaskInput,
) -> SupportCaseLineage | None:
    if not support_input.parent_task_id:
        return None

    parent_task = task_repository.get_task(support_input.parent_task_id)
    if parent_task is None or parent_task.workspace_id != workspace_id:
        raise SupportCopilotContractError("当前工作区中未找到父级 Support 任务")
    if get_scenario_task_module_type(parent_task.task_type) != MODULE_TYPE_SUPPORT:
        raise SupportCopilotContractError("父任务必须是已完成的 Support 任务")
    if parent_task.status != "done":
        raise SupportCopilotContractError("父级 Support 任务必须先完成后才能继续跟进")

    result = parent_task.output_json.get("result")
    if not isinstance(result, dict) or result.get("module_type") != MODULE_TYPE_SUPPORT:
        raise SupportCopilotContractError("父级 Support 任务不包含结构化 Support 结果")

    title = result.get("title")
    summary = result.get("summary")
    if not isinstance(title, str) or not title.strip():
        raise SupportCopilotContractError("父级 Support 任务缺少标题")
    if not isinstance(summary, str) or not summary.strip():
        raise SupportCopilotContractError("父级 Support 任务缺少摘要")

    parent_input = result.get("input")
    parent_input_json = parent_input if isinstance(parent_input, dict) else {}
    triage = result.get("triage")
    triage_json = triage if isinstance(triage, dict) else {}

    return SupportCaseLineage(
        parent_task_id=parent_task.id,
        parent_task_type=cast(SupportTaskType, parent_task.task_type),
        parent_title=title.strip(),
        parent_summary=summary.strip(),
        parent_customer_issue=_normalize_optional_string(
            cast(str | None, parent_input_json.get("customer_issue")),
        ),
        parent_product_area=_normalize_optional_string(
            cast(str | None, parent_input_json.get("product_area")),
        ),
        parent_severity=_coerce_support_severity(parent_input_json.get("severity")),
        parent_desired_outcome=_normalize_optional_string(
            cast(str | None, parent_input_json.get("desired_outcome")),
        ),
        parent_reproduction_steps=_coerce_string_list(parent_input_json.get("reproduction_steps")),
        parent_recommended_owner=_normalize_optional_string(
            cast(str | None, triage_json.get("recommended_owner")),
        ),
        parent_evidence_status=_coerce_support_evidence_status(triage_json.get("evidence_status")),
        follow_up_notes=support_input.follow_up_notes,
    )


def merge_support_task_input_with_lineage(
    *,
    support_input: SupportTaskInput,
    lineage: SupportCaseLineage | None,
) -> SupportTaskInput:
    if lineage is None:
        return support_input

    return SupportTaskInput(
        customer_issue=support_input.customer_issue or lineage.parent_customer_issue,
        product_area=support_input.product_area or lineage.parent_product_area,
        severity=support_input.severity or lineage.parent_severity,
        desired_outcome=support_input.desired_outcome or lineage.parent_desired_outcome,
        reproduction_steps=list(
            support_input.reproduction_steps or lineage.parent_reproduction_steps,
        ),
        parent_task_id=support_input.parent_task_id,
        follow_up_notes=support_input.follow_up_notes,
    )


def build_support_task_search_query(
    support_input: SupportTaskInput,
    *,
    lineage: SupportCaseLineage | None = None,
) -> str:
    query_parts: list[str] = []
    if support_input.customer_issue:
        query_parts.append(support_input.customer_issue)
    if support_input.product_area:
        query_parts.append(f"Product area: {support_input.product_area}")
    if support_input.severity:
        query_parts.append(f"Severity: {support_input.severity}")
    if support_input.desired_outcome:
        query_parts.append(f"Desired outcome: {support_input.desired_outcome}")
    if support_input.reproduction_steps:
        query_parts.append(
            "Reproduction steps: " + "; ".join(support_input.reproduction_steps),
        )
    base_query = " | ".join(query_parts)
    if not base_query:
        base_query = "Review the current support case and recommend the next grounded action."

    if lineage is None:
        return base_query

    follow_up_parts = [
        f"Continue the prior support case '{lineage.parent_title}'.",
        f"Prior summary: {lineage.parent_summary}",
    ]
    if lineage.parent_recommended_owner:
        follow_up_parts.append(f"Prior recommended owner: {lineage.parent_recommended_owner}")
    if lineage.follow_up_notes:
        follow_up_parts.append(f"Follow-up guidance: {lineage.follow_up_notes}")
    follow_up_parts.append(f"Current request: {base_query}")
    return " ".join(follow_up_parts)


def _derive_evidence_status(
    *,
    has_documents: bool,
    has_matches: bool,
) -> SupportEvidenceStatus:
    if has_matches:
        return "grounded_matches"
    if has_documents:
        return "documents_only"
    return "no_documents"


def _build_case_brief(
    *,
    support_input: SupportTaskInput,
    evidence_status: SupportEvidenceStatus,
) -> SupportCaseBrief:
    return SupportCaseBrief(
        issue_summary=support_input.customer_issue or "Support issue was not specified.",
        product_area=support_input.product_area,
        severity=support_input.severity,
        desired_outcome=support_input.desired_outcome,
        reproduction_steps=list(support_input.reproduction_steps),
        evidence_status=evidence_status,
    )


def _build_support_findings(
    *,
    document_models: list[ToolDocumentSummary],
    match_models: list[SearchDocumentMatch],
    evidence_status: SupportEvidenceStatus,
) -> list[SupportFinding]:
    if match_models:
        return [
            SupportFinding(
                title=f"Guidance from {match.document_title}",
                summary=match.snippet,
                evidence_ref_ids=[match.chunk_id],
            )
            for match in match_models[:3]
        ]

    if evidence_status == "documents_only":
        return [
            SupportFinding(
                title="No direct grounded answer found",
                summary=(
                    f"Reviewed {len(document_models)} indexed support document(s), "
                    "but none produced a confident direct match for this case."
                ),
            )
        ]

    return [
        SupportFinding(
            title="No indexed support knowledge available",
            summary=(
                "This workspace does not have indexed support documents, so the case cannot "
                "be grounded yet."
            ),
        )
    ]


def _build_triage_decision(
    *,
    task_type: SupportTaskType,
    severity: SupportSeverity | None,
    evidence_status: SupportEvidenceStatus,
) -> SupportTriageDecision:
    high_severity = severity in {"high", "critical"}
    if evidence_status == "grounded_matches" and not high_severity:
        return SupportTriageDecision(
            evidence_status=evidence_status,
            needs_manual_review=False,
            should_escalate=False,
            recommended_owner="support_frontline",
            rationale="Grounded support guidance exists for a standard frontline follow-up.",
        )

    if evidence_status == "no_documents":
        return SupportTriageDecision(
            evidence_status=evidence_status,
            needs_manual_review=True,
            should_escalate=True,
            recommended_owner="knowledge_base_owner",
            rationale=(
                "No indexed support knowledge is available, so this case needs manual handling "
                "and knowledge coverage follow-up."
            ),
        )

    if high_severity:
        return SupportTriageDecision(
            evidence_status=evidence_status,
            needs_manual_review=True,
            should_escalate=True,
            recommended_owner="support_escalation",
            rationale=(
                "The case severity is high enough that a human reviewer should confirm the "
                "next action before the case proceeds."
            ),
        )

    recommended_owner = "support_specialist" if task_type == "reply_draft" else "support_frontline"
    return SupportTriageDecision(
        evidence_status=evidence_status,
        needs_manual_review=True,
        should_escalate=False,
        recommended_owner=recommended_owner,
        rationale=(
            "Support documents exist, but the grounded evidence is incomplete, so a specialist "
            "should verify the next action."
        ),
    )


def _build_open_questions(
    *,
    support_input: SupportTaskInput,
    evidence_status: SupportEvidenceStatus,
) -> list[str]:
    open_questions: list[str] = []
    if not support_input.product_area:
        open_questions.append("Which product area or feature is affected?")
    if not support_input.desired_outcome:
        open_questions.append("What outcome does the customer expect from this case?")
    if not support_input.reproduction_steps:
        open_questions.append("What exact steps reproduce the issue?")
    if evidence_status != "grounded_matches":
        open_questions.append("Is there an error code, screenshot, or timestamp that narrows the search?")
    if support_input.severity in {"high", "critical"}:
        open_questions.append("What is the current business impact or outage scope?")
    return open_questions


def _build_next_steps(
    *,
    task_type: SupportTaskType,
    findings: list[SupportFinding],
    triage: SupportTriageDecision,
    evidence_status: SupportEvidenceStatus,
    lineage: SupportCaseLineage | None,
) -> list[str]:
    next_steps: list[str] = []
    if lineage is not None:
        next_steps.append(f"Compare this follow-up with parent support task {lineage.parent_task_id}.")
    if evidence_status == "grounded_matches" and findings:
        next_steps.append(f"Use the grounded guidance from '{findings[0].title}' when updating the case.")
    if evidence_status == "documents_only":
        next_steps.append("Collect missing reproduction details or a clearer error signal, then rerun the task.")
    if evidence_status == "no_documents":
        next_steps.append("Index support runbooks or troubleshooting notes for this workspace before rerunning.")
    if task_type == "reply_draft":
        next_steps.append("Review the drafted response before sending it to the customer.")
    if triage.needs_manual_review:
        next_steps.append(f"Route the case to {triage.recommended_owner} for manual review.")
    return next_steps


def _build_reply_draft(
    *,
    support_input: SupportTaskInput,
    findings: list[SupportFinding],
    triage: SupportTriageDecision,
    lineage: SupportCaseLineage | None,
) -> SupportReplyDraft:
    issue_summary = support_input.customer_issue or "your reported issue"
    if findings and triage.evidence_status == "grounded_matches":
        body = (
            f"Thanks for reporting {issue_summary}. Based on the indexed support guidance, "
            f"the strongest next step is: {findings[0].summary}"
        )
        confidence_note = "Grounded in indexed support knowledge."
    elif triage.evidence_status == "documents_only":
        body = (
            f"Thanks for reporting {issue_summary}. We reviewed the available support documents, "
            "but we could not confirm a grounded direct fix yet. A specialist should review the "
            "case before a final response is sent."
        )
        confidence_note = "Partial support context exists, but a grounded direct answer was not found."
    else:
        body = (
            f"Thanks for reporting {issue_summary}. This workspace does not yet have indexed "
            "support knowledge for a grounded response, so the case should be handled manually."
        )
        confidence_note = "No indexed support knowledge is available for this case."

    if lineage is not None:
        body = (
            f"We continued review of {issue_summary}. "
            + body
        )

    if triage.should_escalate:
        body += " Because the case needs escalation, please wait for a reviewed update before action is taken."

    return SupportReplyDraft(
        subject_line="Support update for your reported issue",
        body=body,
        confidence_note=confidence_note,
    )


def _flatten_support_evidence_ref_ids(
    *,
    findings: list[SupportFinding],
    evidence: list[ScenarioEvidenceItem],
) -> list[str]:
    ref_ids: list[str] = []
    seen: set[str] = set()
    for finding in findings:
        for ref_id in finding.evidence_ref_ids:
            if ref_id in seen:
                continue
            seen.add(ref_id)
            ref_ids.append(ref_id)
    for item in evidence:
        if item.ref_id in seen:
            continue
        seen.add(item.ref_id)
        ref_ids.append(item.ref_id)
    return ref_ids


def _build_escalation_packet(
    *,
    summary: str,
    findings: list[SupportFinding],
    triage: SupportTriageDecision,
    open_questions: list[str],
    next_steps: list[str],
    evidence: list[ScenarioEvidenceItem],
    lineage: SupportCaseLineage | None,
) -> SupportEscalationPacket:
    if triage.should_escalate:
        escalation_reason = triage.rationale
    elif triage.needs_manual_review:
        escalation_reason = (
            "Escalation is not mandatory yet, but human review is still required before the case proceeds. "
            + triage.rationale
        )
    else:
        escalation_reason = "Grounded evidence is strong enough for frontline handling without escalation."

    if triage.evidence_status == "grounded_matches":
        grounding_note = "Grounded support matches were found in indexed support knowledge."
    elif triage.evidence_status == "documents_only":
        grounding_note = (
            "Support documents were available, but no direct grounded match was found for the case."
        )
    else:
        grounding_note = (
            "No indexed support knowledge was available, so this handoff is based on visible gaps rather than grounded guidance."
        )

    handoff_note = (
        f"Route this case to {triage.recommended_owner}. "
        f"{grounding_note} {triage.rationale}"
    )
    if lineage is not None and lineage.follow_up_notes:
        handoff_note += f" Follow-up focus: {lineage.follow_up_notes}"

    return SupportEscalationPacket(
        recommended_owner=triage.recommended_owner,
        needs_manual_review=triage.needs_manual_review,
        should_escalate=triage.should_escalate,
        evidence_status=triage.evidence_status,
        escalation_reason=escalation_reason,
        case_summary=summary,
        findings=findings[:3],
        unresolved_questions=open_questions,
        recommended_next_steps=next_steps,
        evidence_ref_ids=_flatten_support_evidence_ref_ids(findings=findings, evidence=evidence),
        follow_up_notes=lineage.follow_up_notes if lineage is not None else None,
        handoff_note=handoff_note,
    )


def build_support_task_result(
    *,
    task_type: SupportTaskType,
    support_input: dict[str, object] | None,
    lineage: dict[str, object] | None = None,
    documents: list[dict[str, object]],
    matches: list[dict[str, object]],
    tool_call_ids: list[str],
) -> dict[str, object]:
    validate_support_task_contract(
        workspace_module_type=MODULE_TYPE_SUPPORT,
        task_type=task_type,
    )

    resolved_input = resolve_support_task_input(support_input)
    resolved_lineage = SupportCaseLineage.model_validate(lineage) if lineage else None
    effective_input = merge_support_task_input_with_lineage(
        support_input=resolved_input,
        lineage=resolved_lineage,
    )
    document_models = [ToolDocumentSummary.model_validate(document) for document in documents]
    match_models = [SearchDocumentMatch.model_validate(match) for match in matches]
    evidence_status = _derive_evidence_status(
        has_documents=bool(document_models),
        has_matches=bool(match_models),
    )
    case_brief = _build_case_brief(
        support_input=effective_input,
        evidence_status=evidence_status,
    )
    findings = _build_support_findings(
        document_models=document_models,
        match_models=match_models,
        evidence_status=evidence_status,
    )
    triage = _build_triage_decision(
        task_type=task_type,
        severity=effective_input.severity,
        evidence_status=evidence_status,
    )
    open_questions = _build_open_questions(
        support_input=effective_input,
        evidence_status=evidence_status,
    )
    next_steps = _build_next_steps(
        task_type=task_type,
        findings=findings,
        triage=triage,
        evidence_status=evidence_status,
        lineage=resolved_lineage,
    )
    reply_draft = (
        _build_reply_draft(
            support_input=effective_input,
            findings=findings,
            triage=triage,
            lineage=resolved_lineage,
        )
        if task_type == "reply_draft"
        else None
    )

    if evidence_status == "grounded_matches":
        summary = (
            f"{'Continued the support case' if resolved_lineage is not None else 'Found grounded support guidance'} "
            f"after reviewing {len(document_models)} document(s) and {len(match_models)} relevant match(es)."
        )
    elif evidence_status == "documents_only":
        summary_prefix = (
            "Continued the support case and reviewed"
            if resolved_lineage is not None
            else "Reviewed"
        )
        summary = (
            f"{summary_prefix} {len(document_models)} indexed support document(s), "
            "but no confident grounded answer was found for this case."
        )
    else:
        summary = (
            "No support knowledge documents are available for this workspace."
            if resolved_lineage is None
            else "Continued the support case, but no support knowledge documents are available for this workspace."
        )

    highlights = [
        f"Issue: {case_brief.issue_summary}",
        f"Evidence status: {evidence_status}",
    ]
    if effective_input.product_area:
        highlights.append(f"Product area: {effective_input.product_area}")
    if effective_input.severity:
        highlights.append(f"Severity: {effective_input.severity}")
    if effective_input.desired_outcome:
        highlights.append(f"Desired outcome: {effective_input.desired_outcome}")
    if resolved_lineage is not None:
        highlights.append(f"Follow-up from: {resolved_lineage.parent_title}")
    highlights.extend(finding.title for finding in findings[:2])

    if match_models:
        evidence = [
            ScenarioEvidenceItem(
                kind="support_knowledge_chunk",
                ref_id=match.chunk_id,
                title=match.document_title,
                snippet=match.snippet,
                metadata={
                    "document_id": match.document_id,
                    "chunk_index": match.chunk_index,
                },
            )
            for match in match_models[:3]
        ]
    else:
        evidence = [
            ScenarioEvidenceItem(
                kind="support_document",
                ref_id=document.id,
                title=document.title,
                metadata={
                    "status": document.status,
                    "source_type": document.source_type,
                },
            )
            for document in document_models[:3]
        ]

    artifacts = SupportArtifacts(
        document_count=len(document_models),
        match_count=len(match_models),
        documents=document_models,
        matches=match_models,
        tool_call_ids=tool_call_ids,
        evidence_status=evidence_status,
    )
    escalation_packet = _build_escalation_packet(
        summary=summary,
        findings=findings,
        triage=triage,
        open_questions=open_questions,
        next_steps=next_steps,
        evidence=evidence,
        lineage=resolved_lineage,
    )
    result = SupportCopilotResult(
        task_type=task_type,
        title=_SUPPORT_TASK_TITLES[task_type],
        input=effective_input,
        lineage=resolved_lineage,
        case_brief=case_brief,
        findings=findings,
        triage=triage,
        open_questions=open_questions,
        next_steps=next_steps,
        reply_draft=reply_draft,
        escalation_packet=escalation_packet,
        summary=summary,
        highlights=highlights,
        evidence=evidence,
        artifacts=artifacts,
        metadata={
            "customer_issue": effective_input.customer_issue,
            "product_area": effective_input.product_area,
            "severity": effective_input.severity,
            "desired_outcome": effective_input.desired_outcome,
            "reproduction_step_count": len(effective_input.reproduction_steps),
            "document_count": len(document_models),
            "match_count": len(match_models),
            "evidence_status": evidence_status,
            "is_follow_up": resolved_lineage is not None,
            "parent_task_id": resolved_lineage.parent_task_id if resolved_lineage is not None else None,
            "follow_up_notes": effective_input.follow_up_notes,
            "manual_review_required": triage.needs_manual_review,
            "should_escalate": triage.should_escalate,
            "escalation_owner": triage.recommended_owner,
            "escalation_packet_ready": True,
        },
    )
    return result.model_dump(exclude_none=True)
