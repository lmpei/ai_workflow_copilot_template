from collections.abc import Sequence

from pydantic import ValidationError

from app.schemas.scenario import (
    MODULE_TYPE_SUPPORT,
    ScenarioEvidenceItem,
    get_scenario_task_module_type,
    get_supported_scenario_task_types,
)
from app.schemas.support import (
    SupportArtifacts,
    SupportCaseBrief,
    SupportCopilotResult,
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
    }
    try:
        payload = SupportTaskInput.model_validate(payload_input)
    except ValidationError as error:
        raise SupportCopilotContractError("Invalid support task input") from error

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

    return normalized_payload


def resolve_support_task_input(input_json: dict[str, object] | None) -> SupportTaskInput:
    try:
        return SupportTaskInput.model_validate(normalize_support_task_input(input_json))
    except ValidationError as error:
        raise SupportCopilotContractError("Invalid support task input") from error


def build_support_task_search_query(support_input: SupportTaskInput) -> str:
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
    return " | ".join(query_parts)


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
) -> list[str]:
    next_steps: list[str] = []
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

    if triage.should_escalate:
        body += " Because the case needs escalation, please wait for a reviewed update before action is taken."

    return SupportReplyDraft(
        subject_line="Support update for your reported issue",
        body=body,
        confidence_note=confidence_note,
    )


def build_support_task_result(
    *,
    task_type: SupportTaskType,
    support_input: dict[str, object] | None,
    documents: list[dict[str, object]],
    matches: list[dict[str, object]],
    tool_call_ids: list[str],
) -> dict[str, object]:
    validate_support_task_contract(
        workspace_module_type=MODULE_TYPE_SUPPORT,
        task_type=task_type,
    )

    resolved_input = resolve_support_task_input(support_input)
    document_models = [ToolDocumentSummary.model_validate(document) for document in documents]
    match_models = [SearchDocumentMatch.model_validate(match) for match in matches]
    evidence_status = _derive_evidence_status(
        has_documents=bool(document_models),
        has_matches=bool(match_models),
    )
    case_brief = _build_case_brief(
        support_input=resolved_input,
        evidence_status=evidence_status,
    )
    findings = _build_support_findings(
        document_models=document_models,
        match_models=match_models,
        evidence_status=evidence_status,
    )
    triage = _build_triage_decision(
        task_type=task_type,
        severity=resolved_input.severity,
        evidence_status=evidence_status,
    )
    open_questions = _build_open_questions(
        support_input=resolved_input,
        evidence_status=evidence_status,
    )
    next_steps = _build_next_steps(
        task_type=task_type,
        findings=findings,
        triage=triage,
        evidence_status=evidence_status,
    )
    reply_draft = (
        _build_reply_draft(
            support_input=resolved_input,
            findings=findings,
            triage=triage,
        )
        if task_type == "reply_draft"
        else None
    )

    if evidence_status == "grounded_matches":
        summary = (
            f"Found grounded support guidance for the case after reviewing "
            f"{len(document_models)} document(s) and {len(match_models)} relevant match(es)."
        )
    elif evidence_status == "documents_only":
        summary = (
            f"Reviewed {len(document_models)} indexed support document(s), but no confident grounded "
            "answer was found for this case."
        )
    else:
        summary = "No support knowledge documents are available for this workspace."

    highlights = [
        f"Issue: {case_brief.issue_summary}",
        f"Evidence status: {evidence_status}",
    ]
    if resolved_input.product_area:
        highlights.append(f"Product area: {resolved_input.product_area}")
    if resolved_input.severity:
        highlights.append(f"Severity: {resolved_input.severity}")
    if resolved_input.desired_outcome:
        highlights.append(f"Desired outcome: {resolved_input.desired_outcome}")
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
    result = SupportCopilotResult(
        task_type=task_type,
        title=_SUPPORT_TASK_TITLES[task_type],
        input=resolved_input,
        case_brief=case_brief,
        findings=findings,
        triage=triage,
        open_questions=open_questions,
        next_steps=next_steps,
        reply_draft=reply_draft,
        summary=summary,
        highlights=highlights,
        evidence=evidence,
        artifacts=artifacts,
        metadata={
            "customer_issue": resolved_input.customer_issue,
            "product_area": resolved_input.product_area,
            "severity": resolved_input.severity,
            "desired_outcome": resolved_input.desired_outcome,
            "reproduction_step_count": len(resolved_input.reproduction_steps),
            "document_count": len(document_models),
            "match_count": len(match_models),
            "evidence_status": evidence_status,
            "manual_review_required": triage.needs_manual_review,
            "should_escalate": triage.should_escalate,
        },
    )
    return result.model_dump(exclude_none=True)
