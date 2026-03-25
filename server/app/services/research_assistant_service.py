from typing import Sequence

from pydantic import ValidationError

from app.schemas.research import (
    ResearchArtifacts,
    ResearchAssistantResult,
    ResearchDeliverable,
    ResearchFinding,
    ResearchFormalReport,
    ResearchLineage,
    ResearchReportSection,
    ResearchRequestedSection,
    ResearchResultSections,
    ResearchTaskInput,
    ResearchTaskType,
)
from app.schemas.scenario import (
    MODULE_TYPE_RESEARCH,
    ScenarioEvidenceItem,
    get_supported_scenario_task_types,
)
from app.schemas.tool import SearchDocumentMatch, ToolDocumentSummary

SUPPORTED_RESEARCH_TASK_TYPES = {
    "research_summary",
    "workspace_report",
}

_RESEARCH_TASK_TITLES = {
    "research_summary": "Research Summary",
    "workspace_report": "Workspace Report",
}
_DEFAULT_RESEARCH_DELIVERABLES: dict[ResearchTaskType, ResearchDeliverable] = {
    "research_summary": "brief",
    "workspace_report": "report",
}
_DEFAULT_RESEARCH_REQUESTED_SECTIONS: dict[ResearchTaskType, list[ResearchRequestedSection]] = {
    "research_summary": ["summary", "findings", "evidence", "next_steps"],
    "workspace_report": ["summary", "findings", "evidence", "open_questions", "next_steps"],
}
RESEARCH_TRUST_BASELINE_VERSION = "stage_a_research_v1"
RESEARCH_REGRESSION_BASELINE_VERSION = "stage_a_research_regression_v1"


class ResearchAssistantContractError(ValueError):
    pass


def validate_research_task_contract(*, workspace_module_type: str, task_type: str) -> None:
    supported_for_module = set(get_supported_scenario_task_types(workspace_module_type))
    if task_type not in supported_for_module:
        raise ResearchAssistantContractError(
            f"Task type {task_type} is not supported for workspace module {workspace_module_type}",
        )
    if task_type not in SUPPORTED_RESEARCH_TASK_TYPES:
        raise ResearchAssistantContractError(
            f"Research Assistant does not support task type: {task_type}",
        )
    if workspace_module_type != MODULE_TYPE_RESEARCH:
        raise ResearchAssistantContractError(
            f"Research Assistant requires workspace module {MODULE_TYPE_RESEARCH}",
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


def normalize_research_task_input(input_json: dict[str, object] | None) -> dict[str, object]:
    try:
        payload = ResearchTaskInput.model_validate(input_json or {})
    except ValidationError as error:
        raise ResearchAssistantContractError("Invalid research task input") from error

    normalized_payload: dict[str, object] = {}

    normalized_goal = _normalize_optional_string(payload.goal)
    if normalized_goal:
        normalized_payload["goal"] = normalized_goal

    focus_areas = _normalize_string_list(payload.focus_areas)
    if focus_areas:
        normalized_payload["focus_areas"] = focus_areas

    key_questions = _normalize_string_list(payload.key_questions)
    if key_questions:
        normalized_payload["key_questions"] = key_questions

    constraints = _normalize_string_list(payload.constraints)
    if constraints:
        normalized_payload["constraints"] = constraints

    if payload.deliverable is not None:
        normalized_payload["deliverable"] = payload.deliverable

    requested_sections = _normalize_string_list(payload.requested_sections)
    if requested_sections:
        normalized_payload["requested_sections"] = requested_sections

    normalized_parent_task_id = _normalize_optional_string(payload.parent_task_id)
    if normalized_parent_task_id:
        normalized_payload["parent_task_id"] = normalized_parent_task_id

    normalized_research_asset_id = _normalize_optional_string(payload.research_asset_id)
    if normalized_research_asset_id:
        normalized_payload["research_asset_id"] = normalized_research_asset_id

    normalized_continuation_notes = _normalize_optional_string(payload.continuation_notes)
    if normalized_continuation_notes:
        normalized_payload["continuation_notes"] = normalized_continuation_notes

    return normalized_payload


def resolve_research_task_input(
    *,
    task_type: ResearchTaskType,
    input_json: dict[str, object] | None,
) -> ResearchTaskInput:
    validate_research_task_contract(
        workspace_module_type=MODULE_TYPE_RESEARCH,
        task_type=task_type,
    )

    normalized_input = normalize_research_task_input(input_json)
    payload = ResearchTaskInput.model_validate(normalized_input)
    return ResearchTaskInput(
        goal=payload.goal,
        focus_areas=payload.focus_areas,
        key_questions=payload.key_questions,
        constraints=payload.constraints,
        deliverable=payload.deliverable or _DEFAULT_RESEARCH_DELIVERABLES[task_type],
        requested_sections=payload.requested_sections
        or list(_DEFAULT_RESEARCH_REQUESTED_SECTIONS[task_type]),
        research_asset_id=payload.research_asset_id,
        parent_task_id=payload.parent_task_id,
        continuation_notes=payload.continuation_notes,
    )


def build_research_task_search_query(
    *,
    task_type: ResearchTaskType,
    research_input: ResearchTaskInput,
    lineage: ResearchLineage | None = None,
) -> str:
    if research_input.goal:
        base_query = research_input.goal
    elif research_input.key_questions:
        base_query = research_input.key_questions[0]
    elif research_input.focus_areas:
        base_query = f"Summarize findings about {research_input.focus_areas[0]}."
    elif task_type == "workspace_report":
        base_query = "Create a concise report for the current workspace."
    else:
        base_query = "Summarize the most relevant findings in this workspace."

    if lineage is None:
        return base_query

    follow_up_parts = [
        f"Continue the prior research run '{lineage.parent_title}'.",
        f"Prior summary: {lineage.parent_summary}",
    ]
    if lineage.parent_goal:
        follow_up_parts.append(f"Original goal: {lineage.parent_goal}")
    if lineage.continuation_notes:
        follow_up_parts.append(f"Follow-up guidance: {lineage.continuation_notes}")
    follow_up_parts.append(f"Current request: {base_query}")
    return " ".join(follow_up_parts)


def _build_research_summary(
    *,
    document_models: list[ToolDocumentSummary],
    match_models: list[SearchDocumentMatch],
) -> str:
    if not document_models:
        return "No workspace documents are available for analysis."
    if not match_models:
        return (
            f"Reviewed {len(document_models)} workspace document(s), "
            "but no relevant indexed matches were found for the research request."
        )

    top_match = match_models[0]
    return (
        f"Reviewed {len(document_models)} workspace document(s). "
        f"Top match from {top_match.document_title} says: {top_match.snippet}"
    )


def _build_research_evidence_and_highlights(
    *,
    document_models: list[ToolDocumentSummary],
    match_models: list[SearchDocumentMatch],
) -> tuple[list[str], list[ScenarioEvidenceItem]]:
    if match_models:
        highlights = [
            f"{match.document_title}: {match.snippet}"
            for match in match_models[:3]
        ]
        evidence = [
            ScenarioEvidenceItem(
                kind="document_chunk",
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
        return highlights, evidence

    highlights = [
        f"{document.title} ({document.status})"
        for document in document_models[:3]
    ]
    evidence = [
        ScenarioEvidenceItem(
            kind="document",
            ref_id=document.id,
            title=document.title,
            metadata={
                "status": document.status,
                "source_type": document.source_type,
            },
        )
        for document in document_models[:3]
    ]
    return highlights, evidence


def _build_research_sections(
    *,
    task_type: ResearchTaskType,
    research_input: ResearchTaskInput,
    lineage: ResearchLineage | None,
    summary: str,
    document_models: list[ToolDocumentSummary],
    match_models: list[SearchDocumentMatch],
    evidence: list[ScenarioEvidenceItem],
) -> ResearchResultSections:
    if match_models:
        findings = [
            ResearchFinding(
                title=match.document_title,
                summary=match.snippet,
                evidence_ref_ids=[match.chunk_id],
            )
            for match in match_models[:3]
        ]
        evidence_overview = [
            f"{item.title}: {item.snippet}"
            for item in evidence
            if item.title and item.snippet
        ]
        open_questions = list(research_input.key_questions[1:4])
        next_steps = [
            "Review the linked evidence chunks in the workspace documents view.",
            "Refine the research goal or add follow-up key questions for a narrower pass.",
        ]
        if task_type == "research_summary":
            next_steps.append("Promote this question into a workspace report if broader synthesis is needed.")
        else:
            next_steps.append("Use this report as the baseline for the next research iteration.")
    elif document_models:
        findings = [
            ResearchFinding(
                title=document.title,
                summary=f"Document is available with status {document.status}.",
                evidence_ref_ids=[document.id],
            )
            for document in document_models[:3]
        ]
        evidence_overview = [
            f"{document.title} is indexed as {document.status}."
            for document in document_models[:3]
        ]
        open_questions = list(research_input.key_questions[:3])
        if not open_questions:
            open_questions = [
                "Which query or focus area would narrow the search toward stronger evidence?",
            ]
        next_steps = [
            "Add a clearer research goal or key question to drive targeted retrieval.",
            "Inspect the indexed documents and verify whether more focused chunks should be added.",
        ]
    else:
        findings = []
        evidence_overview = []
        open_questions = list(research_input.key_questions[:3])
        if not open_questions:
            open_questions = [
                "What source documents should be added to support this research request?",
            ]
        next_steps = [
            "Upload or index workspace documents before rerunning this research task.",
            "Clarify the scope and key questions once supporting sources are available.",
        ]

    if lineage is not None:
        if lineage.continuation_notes:
            open_questions = [lineage.continuation_notes, *open_questions]
        next_steps = [
            f"Compare this run against parent research task {lineage.parent_task_id}.",
            *next_steps,
        ]

    return ResearchResultSections(
        summary=summary,
        findings=findings,
        evidence_overview=evidence_overview,
        open_questions=open_questions,
        next_steps=next_steps,
    )


def _flatten_evidence_ref_ids(sections: ResearchResultSections) -> list[str]:
    ref_ids: list[str] = []
    seen: set[str] = set()
    for finding in sections.findings:
        for ref_id in finding.evidence_ref_ids:
            if ref_id in seen:
                continue
            seen.add(ref_id)
            ref_ids.append(ref_id)
    return ref_ids


def _build_report_section(
    *,
    slug: str,
    title: str,
    summary: str,
    bullets: list[str],
    evidence_ref_ids: list[str],
) -> ResearchReportSection:
    unique_ref_ids: list[str] = []
    seen: set[str] = set()
    for ref_id in evidence_ref_ids:
        if ref_id in seen:
            continue
        seen.add(ref_id)
        unique_ref_ids.append(ref_id)

    return ResearchReportSection(
        slug=slug,
        title=title,
        summary=summary,
        bullets=bullets,
        evidence_ref_ids=unique_ref_ids,
    )


def _should_build_formal_report(
    *,
    task_type: ResearchTaskType,
    research_input: ResearchTaskInput,
) -> bool:
    return task_type == "workspace_report" or research_input.deliverable == "report"


def _build_formal_research_report(
    *,
    task_type: ResearchTaskType,
    research_input: ResearchTaskInput,
    lineage: ResearchLineage | None,
    sections: ResearchResultSections,
    evidence: list[ScenarioEvidenceItem],
) -> ResearchFormalReport | None:
    if not _should_build_formal_report(task_type=task_type, research_input=research_input):
        return None

    headline_source = research_input.goal or "Workspace research report"
    headline_prefix = "Research Follow-up Report" if lineage is not None else "Research Report"
    headline = f"{headline_prefix}: {headline_source}"
    section_items: list[ResearchReportSection] = []
    evidence_ref_ids = _flatten_evidence_ref_ids(sections)

    requested_sections = set(research_input.requested_sections)

    if "findings" in requested_sections:
        finding_bullets = [
            f"{finding.title}: {finding.summary}"
            for finding in sections.findings
        ]
        if not finding_bullets:
            finding_bullets = [
                "No grounded findings were available; review the evidence coverage and refine the request.",
            ]
        section_items.append(
            _build_report_section(
                slug="findings",
                title="Key Findings",
                summary="Top findings synthesized from the currently available workspace evidence.",
                bullets=finding_bullets,
                evidence_ref_ids=evidence_ref_ids,
            ),
        )

    if "evidence" in requested_sections:
        evidence_bullets = list(sections.evidence_overview)
        if not evidence_bullets:
            evidence_bullets = [
                "The current run did not identify strong grounded evidence for the requested topic.",
            ]
        section_items.append(
            _build_report_section(
                slug="evidence",
                title="Evidence Base",
                summary="Evidence references that most strongly support the current report draft.",
                bullets=evidence_bullets,
                evidence_ref_ids=[item.ref_id for item in evidence],
            ),
        )

    if "open_questions" in requested_sections:
        open_question_bullets = list(sections.open_questions)
        if not open_question_bullets:
            open_question_bullets = [
                "No additional open questions were surfaced in this run.",
            ]
        section_items.append(
            _build_report_section(
                slug="open-questions",
                title="Open Questions",
                summary="Remaining gaps or follow-up questions that should shape the next research pass.",
                bullets=open_question_bullets,
                evidence_ref_ids=[],
            ),
        )

    if "next_steps" in requested_sections:
        next_step_bullets = list(sections.next_steps)
        if not next_step_bullets:
            next_step_bullets = [
                "No explicit next steps were generated for this run.",
            ]
        section_items.append(
            _build_report_section(
                slug="next-steps",
                title="Recommended Next Steps",
                summary="Suggested follow-up actions to deepen or validate the report.",
                bullets=next_step_bullets,
                evidence_ref_ids=[],
            ),
        )

    return ResearchFormalReport(
        headline=headline,
        executive_summary=sections.summary,
        sections=section_items,
        open_questions=sections.open_questions,
        recommended_next_steps=sections.next_steps,
        evidence_ref_ids=[item.ref_id for item in evidence],
    )


def _build_research_trust_metadata(
    *,
    task_type: ResearchTaskType,
    research_input: ResearchTaskInput,
    lineage: ResearchLineage | None,
    sections: ResearchResultSections,
    report: ResearchFormalReport | None,
    document_models: list[ToolDocumentSummary],
    match_models: list[SearchDocumentMatch],
    evidence: list[ScenarioEvidenceItem],
) -> dict[str, object]:
    report_requested = _should_build_formal_report(
        task_type=task_type,
        research_input=research_input,
    )
    grounded_finding_count = sum(1 for finding in sections.findings if finding.evidence_ref_ids)

    if match_models:
        evidence_status = "grounded_matches"
    elif document_models:
        evidence_status = "documents_only"
    else:
        evidence_status = "no_documents"

    gaps: list[str] = []
    if not document_models:
        gaps.append("no_documents_available")
    elif not match_models:
        gaps.append("no_grounded_matches")

    checks = {
        "summary_present": bool(sections.summary.strip()),
        "findings_or_gap_documented": bool(sections.findings) or bool(gaps),
        "evidence_or_gap_documented": bool(evidence) or bool(gaps),
        "grounded_findings_when_matches_exist": (len(match_models) == 0) or grounded_finding_count > 0,
        "report_present_if_requested": (not report_requested) or report is not None,
        "report_summary_present_if_requested": (
            (not report_requested)
            or (report is not None and bool(report.executive_summary.strip()))
        ),
        "next_steps_present": len(sections.next_steps) > 0,
    }

    return {
        "baseline_version": RESEARCH_TRUST_BASELINE_VERSION,
        "evidence_status": evidence_status,
        "document_count": len(document_models),
        "match_count": len(match_models),
        "evidence_count": len(evidence),
        "finding_count": len(sections.findings),
        "grounded_finding_count": grounded_finding_count,
        "report_requested": report_requested,
        "report_section_count": len(report.sections) if report is not None else 0,
        "is_follow_up": lineage is not None,
        "checks": checks,
        "gaps": gaps,
        "regression_passed": all(checks.values()),
    }


def evaluate_research_result_regression(
    result_json: dict[str, object],
) -> dict[str, object]:
    metadata = result_json.get("metadata")
    metadata_json = metadata if isinstance(metadata, dict) else {}
    trust = metadata_json.get("trust")
    trust_json = trust if isinstance(trust, dict) else {}
    input_json = result_json.get("input")
    input_payload = input_json if isinstance(input_json, dict) else {}
    sections_json = result_json.get("sections")
    sections_payload = sections_json if isinstance(sections_json, dict) else {}
    artifacts_json = result_json.get("artifacts")
    artifacts_payload = artifacts_json if isinstance(artifacts_json, dict) else {}
    report_json = result_json.get("report")
    report_payload = report_json if isinstance(report_json, dict) else {}
    lineage_json = result_json.get("lineage")

    task_type = result_json.get("task_type")
    summary = result_json.get("summary")
    evidence_status = metadata_json.get("evidence_status")
    trust_gaps = metadata_json.get("trust_gaps")
    if not isinstance(trust_gaps, list):
        trust_gaps = trust_json.get("gaps", [])
    trust_gap_values = [
        str(item).strip()
        for item in trust_gaps
        if isinstance(item, str) and item.strip()
    ]

    findings = sections_payload.get("findings")
    finding_list = findings if isinstance(findings, list) else []
    grounded_finding_count = sum(
        1
        for finding in finding_list
        if isinstance(finding, dict)
        and isinstance(finding.get("evidence_ref_ids"), list)
        and len(finding["evidence_ref_ids"]) > 0
    )

    match_count_raw = artifacts_payload.get("match_count")
    match_count = match_count_raw if isinstance(match_count_raw, int) else 0
    deliverable = input_payload.get("deliverable")
    report_expected = task_type == "workspace_report" or deliverable == "report"
    report_sections = (
        report_payload.get("sections")
    )
    report_section_list = report_sections if isinstance(report_sections, list) else []
    is_follow_up = metadata_json.get("is_follow_up") is True or input_payload.get("parent_task_id") is not None

    checks = {
        "module_type_valid": result_json.get("module_type") == "research",
        "task_type_valid": task_type in SUPPORTED_RESEARCH_TASK_TYPES,
        "summary_present": isinstance(summary, str) and bool(summary.strip()),
        "sections_present": isinstance(sections_json, dict)
        and isinstance(sections_payload.get("summary"), str)
        and bool(str(sections_payload.get("summary")).strip()),
        "artifacts_present": isinstance(artifacts_json, dict),
        "trust_present": isinstance(trust, dict),
        "trust_baseline_present": trust_json.get("baseline_version") == RESEARCH_TRUST_BASELINE_VERSION,
        "evidence_status_known": evidence_status in {"grounded_matches", "documents_only", "no_documents"},
        "grounded_evidence_required": evidence_status == "grounded_matches",
        "grounded_findings_present_when_matches_exist": match_count == 0 or grounded_finding_count > 0,
        "report_present_when_expected": (not report_expected) or isinstance(report_json, dict),
        "report_shape_valid_when_expected": (not report_expected)
        or (
            isinstance(report_json, dict)
            and isinstance(report_payload.get("executive_summary"), str)
            and bool(str(report_payload.get("executive_summary")).strip())
            and len(report_section_list) > 0
        ),
        "weak_context_flagged": (evidence_status == "grounded_matches") or len(trust_gap_values) > 0,
        "lineage_present_for_follow_up": (not is_follow_up) or isinstance(lineage_json, dict),
    }

    issues: list[str] = []
    if checks["grounded_evidence_required"] is False:
        if evidence_status == "documents_only":
            issues.append("weak_evidence_documents_only")
        elif evidence_status == "no_documents":
            issues.append("no_documents_available")
        else:
            issues.append("grounded_evidence_missing")
    if checks["grounded_findings_present_when_matches_exist"] is False:
        issues.append("grounded_findings_missing")
    if checks["report_present_when_expected"] is False:
        issues.append("missing_report")
    if checks["report_shape_valid_when_expected"] is False:
        issues.append("invalid_report_shape")
    if checks["trust_present"] is False:
        issues.append("missing_trust_metadata")
    if checks["trust_baseline_present"] is False:
        issues.append("unexpected_trust_baseline")
    if checks["summary_present"] is False:
        issues.append("missing_summary")
    if checks["sections_present"] is False:
        issues.append("missing_sections_summary")
    if checks["weak_context_flagged"] is False:
        issues.append("weak_context_not_flagged")
    if checks["lineage_present_for_follow_up"] is False:
        issues.append("missing_follow_up_lineage")

    passed = all(checks.values())

    return {
        "baseline_version": RESEARCH_REGRESSION_BASELINE_VERSION,
        "passed": passed,
        "checks": checks,
        "issues": issues,
        "signals": {
            "task_type": task_type,
            "deliverable": deliverable,
            "evidence_status": evidence_status,
            "match_count": match_count,
            "grounded_finding_count": grounded_finding_count,
            "report_expected": report_expected,
            "report_section_count": len(report_section_list),
            "trust_gap_count": len(trust_gap_values),
            "is_follow_up": is_follow_up,
        },
    }


def build_research_task_result(
    *,
    task_type: ResearchTaskType,
    research_input: dict[str, object] | None,
    lineage: dict[str, object] | None = None,
    documents: list[dict[str, object]],
    matches: list[dict[str, object]],
    tool_call_ids: list[str],
) -> dict[str, object]:
    resolved_input = resolve_research_task_input(
        task_type=task_type,
        input_json=research_input,
    )
    resolved_lineage = ResearchLineage.model_validate(lineage) if lineage else None

    document_models = [ToolDocumentSummary.model_validate(document) for document in documents]
    match_models = [SearchDocumentMatch.model_validate(match) for match in matches]
    summary = _build_research_summary(
        document_models=document_models,
        match_models=match_models,
    )
    highlights, evidence = _build_research_evidence_and_highlights(
        document_models=document_models,
        match_models=match_models,
    )
    sections = _build_research_sections(
        task_type=task_type,
        research_input=resolved_input,
        lineage=resolved_lineage,
        summary=summary,
        document_models=document_models,
        match_models=match_models,
        evidence=evidence,
    )
    report = _build_formal_research_report(
        task_type=task_type,
        research_input=resolved_input,
        lineage=resolved_lineage,
        sections=sections,
        evidence=evidence,
    )
    trust_metadata = _build_research_trust_metadata(
        task_type=task_type,
        research_input=resolved_input,
        lineage=resolved_lineage,
        sections=sections,
        report=report,
        document_models=document_models,
        match_models=match_models,
        evidence=evidence,
    )
    trust_gaps_raw = trust_metadata.get("gaps")
    trust_gaps = [
        gap
        for gap in trust_gaps_raw
        if isinstance(gap, str)
    ] if isinstance(trust_gaps_raw, list) else []

    artifacts = ResearchArtifacts(
        document_count=len(document_models),
        match_count=len(match_models),
        documents=document_models,
        matches=match_models,
        tool_call_ids=tool_call_ids,
    )
    result = ResearchAssistantResult(
        task_type=task_type,
        title=_RESEARCH_TASK_TITLES[task_type],
        input=resolved_input,
        lineage=resolved_lineage,
        summary=summary,
        sections=sections,
        report=report,
        highlights=highlights,
        evidence=evidence,
        artifacts=artifacts,
        metadata={
            "goal": resolved_input.goal,
            "deliverable": resolved_input.deliverable,
            "requested_sections": list(resolved_input.requested_sections),
            "focus_area_count": len(resolved_input.focus_areas),
            "key_question_count": len(resolved_input.key_questions),
            "document_count": len(document_models),
            "match_count": len(match_models),
            "is_follow_up": resolved_lineage is not None,
            "parent_task_id": resolved_lineage.parent_task_id if resolved_lineage is not None else None,
            "evidence_status": trust_metadata["evidence_status"],
            "report_ready": report is not None,
            "regression_passed": trust_metadata["regression_passed"],
            "trust_gaps": trust_gaps,
            "trust": trust_metadata,
        },
    )
    result_json = result.model_dump(exclude_none=True)
    regression_baseline = evaluate_research_result_regression(result_json)
    result_metadata = result_json.get("metadata")
    if isinstance(result_metadata, dict):
        result_metadata["regression_passed"] = regression_baseline["passed"]
        result_metadata["regression_baseline"] = regression_baseline
        trust_json = result_metadata.get("trust")
        if isinstance(trust_json, dict):
            trust_json["regression_passed"] = regression_baseline["passed"]
    return result_json
