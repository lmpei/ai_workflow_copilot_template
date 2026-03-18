from pydantic import ValidationError

from app.schemas.research import (
    ResearchArtifacts,
    ResearchAssistantResult,
    ResearchDeliverable,
    ResearchFinding,
    ResearchFormalReport,
    ResearchReportSection,
    ResearchResultSections,
    ResearchTaskInput,
    ResearchRequestedSection,
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
    )


def build_research_task_search_query(
    *,
    task_type: ResearchTaskType,
    research_input: ResearchTaskInput,
) -> str:
    if research_input.goal:
        return research_input.goal
    if research_input.key_questions:
        return research_input.key_questions[0]
    if research_input.focus_areas:
        return f"Summarize findings about {research_input.focus_areas[0]}."
    if task_type == "workspace_report":
        return "Create a concise report for the current workspace."
    return "Summarize the most relevant findings in this workspace."


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
    sections: ResearchResultSections,
    evidence: list[ScenarioEvidenceItem],
) -> ResearchFormalReport | None:
    if not _should_build_formal_report(task_type=task_type, research_input=research_input):
        return None

    headline_source = research_input.goal or "Workspace research report"
    headline = f"Research Report: {headline_source}"
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
        "checks": checks,
        "gaps": gaps,
        "regression_passed": all(checks.values()),
    }


def build_research_task_result(
    *,
    task_type: ResearchTaskType,
    research_input: dict[str, object] | None,
    documents: list[dict[str, object]],
    matches: list[dict[str, object]],
    tool_call_ids: list[str],
) -> dict[str, object]:
    resolved_input = resolve_research_task_input(
        task_type=task_type,
        input_json=research_input,
    )

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
        summary=summary,
        document_models=document_models,
        match_models=match_models,
        evidence=evidence,
    )
    report = _build_formal_research_report(
        task_type=task_type,
        research_input=resolved_input,
        sections=sections,
        evidence=evidence,
    )
    trust_metadata = _build_research_trust_metadata(
        task_type=task_type,
        research_input=resolved_input,
        sections=sections,
        report=report,
        document_models=document_models,
        match_models=match_models,
        evidence=evidence,
    )

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
            "evidence_status": trust_metadata["evidence_status"],
            "report_ready": report is not None,
            "regression_passed": trust_metadata["regression_passed"],
            "trust_gaps": list(trust_metadata["gaps"]),
            "trust": trust_metadata,
        },
    )
    return result.model_dump(exclude_none=True)
