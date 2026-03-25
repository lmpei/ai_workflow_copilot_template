from collections.abc import Sequence

from pydantic import ValidationError

from app.schemas.job import (
    JobArtifacts,
    JobAssistantResult,
    JobEvidenceStatus,
    JobFinding,
    JobFitAssessment,
    JobFitSignal,
    JobReviewBrief,
    JobTaskInput,
    JobTaskType,
)
from app.schemas.scenario import (
    MODULE_TYPE_JOB,
    ScenarioEvidenceItem,
    get_scenario_task_module_type,
    get_supported_scenario_task_types,
)
from app.schemas.tool import SearchDocumentMatch, ToolDocumentSummary

_JOB_TASK_TITLES = {
    "jd_summary": "Job Description Summary",
    "resume_match": "Structured Resume Match Review",
}


class JobAssistantContractError(ValueError):
    pass


def validate_job_task_contract(*, workspace_module_type: str, task_type: str) -> None:
    supported_for_module = set(get_supported_scenario_task_types(workspace_module_type))
    if task_type not in supported_for_module:
        raise JobAssistantContractError(
            f"Task type {task_type} is not supported for workspace module {workspace_module_type}",
        )
    if get_scenario_task_module_type(task_type) != MODULE_TYPE_JOB:
        raise JobAssistantContractError(
            f"Job Assistant does not support task type: {task_type}",
        )
    if workspace_module_type != MODULE_TYPE_JOB:
        raise JobAssistantContractError(
            f"Job Assistant requires workspace module {MODULE_TYPE_JOB}",
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


def normalize_job_task_input(input_json: dict[str, object] | None) -> dict[str, object]:
    raw_input = input_json or {}
    if raw_input.get("target_role") is None and isinstance(raw_input.get("goal"), str):
        raise JobAssistantContractError(
            "Job task input must use target_role instead of goal",
        )

    payload_input = {
        "target_role": raw_input.get("target_role"),
        "seniority": raw_input.get("seniority"),
        "must_have_skills": raw_input.get("must_have_skills", []),
        "preferred_skills": raw_input.get("preferred_skills", []),
        "hiring_context": raw_input.get("hiring_context"),
    }
    try:
        payload = JobTaskInput.model_validate(payload_input)
    except ValidationError as error:
        raise JobAssistantContractError("Invalid job task input") from error

    normalized_payload: dict[str, object] = {}

    normalized_target_role = _normalize_optional_string(payload.target_role)
    if normalized_target_role:
        normalized_payload["target_role"] = normalized_target_role

    normalized_seniority = _normalize_optional_string(payload.seniority)
    if normalized_seniority:
        normalized_payload["seniority"] = normalized_seniority

    normalized_must_have_skills = _normalize_string_list(payload.must_have_skills)
    if normalized_must_have_skills:
        normalized_payload["must_have_skills"] = normalized_must_have_skills

    normalized_preferred_skills = _normalize_string_list(payload.preferred_skills)
    if normalized_preferred_skills:
        normalized_payload["preferred_skills"] = normalized_preferred_skills

    normalized_hiring_context = _normalize_optional_string(payload.hiring_context)
    if normalized_hiring_context:
        normalized_payload["hiring_context"] = normalized_hiring_context

    return normalized_payload


def resolve_job_task_input(input_json: dict[str, object] | None) -> JobTaskInput:
    try:
        return JobTaskInput.model_validate(normalize_job_task_input(input_json))
    except ValidationError as error:
        raise JobAssistantContractError("Invalid job task input") from error


def build_job_task_search_query(job_input: JobTaskInput) -> str:
    query_parts: list[str] = []
    if job_input.target_role:
        query_parts.append(job_input.target_role)
    if job_input.seniority:
        query_parts.append(f"Seniority: {job_input.seniority}")
    if job_input.must_have_skills:
        query_parts.append("Must-have skills: " + ", ".join(job_input.must_have_skills))
    if job_input.preferred_skills:
        query_parts.append("Preferred skills: " + ", ".join(job_input.preferred_skills))
    if job_input.hiring_context:
        query_parts.append(f"Hiring context: {job_input.hiring_context}")
    return " | ".join(query_parts)


def _derive_evidence_status(*, has_documents: bool, has_matches: bool) -> JobEvidenceStatus:
    if has_matches:
        return "grounded_matches"
    if has_documents:
        return "documents_only"
    return "no_documents"


def _build_review_brief(
    *,
    job_input: JobTaskInput,
    evidence_status: JobEvidenceStatus,
) -> JobReviewBrief:
    return JobReviewBrief(
        role_summary=job_input.target_role or "General hiring review",
        seniority=job_input.seniority,
        must_have_skills=list(job_input.must_have_skills),
        preferred_skills=list(job_input.preferred_skills),
        hiring_context=job_input.hiring_context,
        evidence_status=evidence_status,
    )


def _build_job_findings(
    *,
    task_type: JobTaskType,
    document_models: list[ToolDocumentSummary],
    match_models: list[SearchDocumentMatch],
    evidence_status: JobEvidenceStatus,
) -> list[JobFinding]:
    if match_models:
        finding_prefix = "Candidate signal" if task_type == "resume_match" else "Role signal"
        return [
            JobFinding(
                title=f"{finding_prefix} from {match.document_title}",
                summary=match.snippet,
                evidence_ref_ids=[match.chunk_id],
            )
            for match in match_models[:3]
        ]

    if evidence_status == "documents_only":
        return [
            JobFinding(
                title="Hiring materials exist but grounding is incomplete",
                summary=(
                    f"Reviewed {len(document_models)} indexed hiring document(s), but none produced "
                    "a confident direct grounded match for the current review."
                ),
            )
        ]

    return [
        JobFinding(
            title="No indexed hiring materials available",
            summary=(
                "This workspace does not have indexed hiring documents yet, so the hiring review "
                "cannot be grounded."
            ),
        )
    ]


def _build_gaps(
    *,
    job_input: JobTaskInput,
    evidence_status: JobEvidenceStatus,
) -> list[str]:
    gaps: list[str] = []
    if not job_input.target_role:
        gaps.append("Target role is not specified.")
    if not job_input.must_have_skills:
        gaps.append("Must-have skills are not specified.")
    if evidence_status == "documents_only":
        gaps.append("Indexed hiring materials exist, but no direct grounded fit evidence was found.")
    if evidence_status == "no_documents":
        gaps.append("No indexed job descriptions, resumes, or hiring notes are available in this workspace.")
    return gaps


def _build_fit_signal(
    *,
    task_type: JobTaskType,
    evidence_status: JobEvidenceStatus,
) -> JobFitSignal:
    if evidence_status == "grounded_matches":
        if task_type == "resume_match":
            return "grounded_match_found"
        return "role_requirements_grounded"
    if evidence_status == "documents_only":
        return "insufficient_grounding"
    return "no_documents_available"


def _build_fit_assessment(
    *,
    task_type: JobTaskType,
    fit_signal: JobFitSignal,
    evidence_status: JobEvidenceStatus,
) -> JobFitAssessment:
    if fit_signal == "grounded_match_found":
        return JobFitAssessment(
            fit_signal=fit_signal,
            evidence_status=evidence_status,
            recommended_outcome="advance_to_manual_review",
            confidence_note="Grounded candidate evidence exists in the indexed hiring materials.",
            rationale="The workspace contains direct grounded evidence that should be reviewed before deciding the next hiring step.",
        )
    if fit_signal == "role_requirements_grounded":
        return JobFitAssessment(
            fit_signal=fit_signal,
            evidence_status=evidence_status,
            recommended_outcome="align_screening_plan",
            confidence_note="Grounded role requirements exist in the indexed hiring materials.",
            rationale="The indexed materials are strong enough to align screening and role-review criteria.",
        )
    if fit_signal == "insufficient_grounding":
        recommended_outcome = "collect_more_hiring_signal" if task_type == "resume_match" else "clarify_role_definition"
        return JobFitAssessment(
            fit_signal=fit_signal,
            evidence_status=evidence_status,
            recommended_outcome=recommended_outcome,
            confidence_note="Some hiring documents exist, but they do not yet support a confident grounded review.",
            rationale="A human reviewer should clarify the role focus or add stronger hiring materials before making a decision.",
        )
    return JobFitAssessment(
        fit_signal=fit_signal,
        evidence_status=evidence_status,
        recommended_outcome="gather_hiring_materials",
        confidence_note="No indexed hiring context is available for a grounded review.",
        rationale="Upload or index job descriptions, resumes, or hiring notes before attempting a structured hiring review.",
    )


def _build_open_questions(
    *,
    job_input: JobTaskInput,
    evidence_status: JobEvidenceStatus,
) -> list[str]:
    open_questions: list[str] = []
    if not job_input.seniority:
        open_questions.append("What seniority level should this role be evaluated against?")
    if not job_input.must_have_skills:
        open_questions.append("Which skills are non-negotiable for this hiring decision?")
    if not job_input.hiring_context:
        open_questions.append("What team or business context should guide this hiring review?")
    if evidence_status != "grounded_matches":
        open_questions.append("Which additional job descriptions, resumes, or interview notes should be indexed?")
    return open_questions


def _build_next_steps(
    *,
    task_type: JobTaskType,
    findings: list[JobFinding],
    assessment: JobFitAssessment,
    evidence_status: JobEvidenceStatus,
) -> list[str]:
    next_steps: list[str] = []
    if evidence_status == "grounded_matches" and findings:
        next_steps.append(f"Review the grounded evidence from '{findings[0].title}' before the hiring discussion.")
    if task_type == "resume_match":
        next_steps.append("Confirm whether the resume evidence is strong enough for the next screening step.")
    else:
        next_steps.append("Use the structured role summary to align screening criteria and interviewer focus.")
    if assessment.recommended_outcome == "collect_more_hiring_signal":
        next_steps.append("Add clearer role-fit criteria or stronger candidate materials, then rerun the task.")
    if assessment.recommended_outcome == "clarify_role_definition":
        next_steps.append("Clarify target role, seniority, or must-have skills before rerunning the task.")
    if assessment.recommended_outcome == "gather_hiring_materials":
        next_steps.append("Index job descriptions, resumes, or hiring notes for this workspace before rerunning.")
    return next_steps


def _build_recommended_next_step(
    *,
    task_type: JobTaskType,
    assessment: JobFitAssessment,
) -> str:
    if assessment.recommended_outcome == "advance_to_manual_review":
        return "Review the grounded fit evidence and decide whether the candidate should advance."
    if assessment.recommended_outcome == "align_screening_plan":
        return "Use the grounded role signals to align the final screening plan and hiring rubric."
    if assessment.recommended_outcome == "clarify_role_definition":
        return "Clarify target role, seniority, or must-have skills before rerunning this hiring review."
    if task_type == "resume_match":
        return "Add clearer candidate evidence or role-fit criteria before rerunning this match review."
    return "Upload job descriptions or candidate materials to produce a grounded hiring result."


def build_job_task_result(
    *,
    task_type: JobTaskType,
    job_input: dict[str, object] | None,
    documents: list[dict[str, object]],
    matches: list[dict[str, object]],
    tool_call_ids: list[str],
) -> dict[str, object]:
    validate_job_task_contract(
        workspace_module_type=MODULE_TYPE_JOB,
        task_type=task_type,
    )

    resolved_input = resolve_job_task_input(job_input)
    document_models = [ToolDocumentSummary.model_validate(document) for document in documents]
    match_models = [SearchDocumentMatch.model_validate(match) for match in matches]
    evidence_status = _derive_evidence_status(
        has_documents=bool(document_models),
        has_matches=bool(match_models),
    )
    review_brief = _build_review_brief(
        job_input=resolved_input,
        evidence_status=evidence_status,
    )
    findings = _build_job_findings(
        task_type=task_type,
        document_models=document_models,
        match_models=match_models,
        evidence_status=evidence_status,
    )
    gaps = _build_gaps(
        job_input=resolved_input,
        evidence_status=evidence_status,
    )
    fit_signal = _build_fit_signal(
        task_type=task_type,
        evidence_status=evidence_status,
    )
    assessment = _build_fit_assessment(
        task_type=task_type,
        fit_signal=fit_signal,
        evidence_status=evidence_status,
    )
    open_questions = _build_open_questions(
        job_input=resolved_input,
        evidence_status=evidence_status,
    )
    next_steps = _build_next_steps(
        task_type=task_type,
        findings=findings,
        assessment=assessment,
        evidence_status=evidence_status,
    )
    recommended_next_step = _build_recommended_next_step(
        task_type=task_type,
        assessment=assessment,
    )

    if evidence_status == "grounded_matches":
        summary = (
            f"Found grounded hiring evidence after reviewing {len(document_models)} document(s) "
            f"and {len(match_models)} relevant match(es)."
        )
    elif evidence_status == "documents_only":
        summary = (
            f"Reviewed {len(document_models)} indexed hiring document(s), but no confident grounded "
            "fit signal was found for the current review."
        )
    else:
        summary = "No job documents are available for this workspace."

    highlights = [
        f"Role focus: {review_brief.role_summary}",
        f"Evidence status: {evidence_status}",
        f"Fit signal: {fit_signal}",
    ]
    if resolved_input.seniority:
        highlights.append(f"Seniority: {resolved_input.seniority}")
    if resolved_input.must_have_skills:
        highlights.append("Must-have skills: " + ", ".join(resolved_input.must_have_skills[:3]))
    highlights.extend(finding.title for finding in findings[:2])

    if match_models:
        evidence = [
            ScenarioEvidenceItem(
                kind="job_context_chunk",
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
                kind="job_document",
                ref_id=document.id,
                title=document.title,
                metadata={
                    "status": document.status,
                    "source_type": document.source_type,
                },
            )
            for document in document_models[:3]
        ]

    artifacts = JobArtifacts(
        document_count=len(document_models),
        match_count=len(match_models),
        documents=document_models,
        matches=match_models,
        tool_call_ids=tool_call_ids,
        evidence_status=evidence_status,
        fit_signal=fit_signal,
        recommended_next_step=recommended_next_step,
    )
    result = JobAssistantResult(
        task_type=task_type,
        title=_JOB_TASK_TITLES[task_type],
        input=resolved_input,
        review_brief=review_brief,
        findings=findings,
        gaps=gaps,
        assessment=assessment,
        open_questions=open_questions,
        next_steps=next_steps,
        summary=summary,
        highlights=highlights,
        evidence=evidence,
        artifacts=artifacts,
        metadata={
            "target_role": resolved_input.target_role,
            "seniority": resolved_input.seniority,
            "must_have_skill_count": len(resolved_input.must_have_skills),
            "preferred_skill_count": len(resolved_input.preferred_skills),
            "document_count": len(document_models),
            "match_count": len(match_models),
            "evidence_status": evidence_status,
            "fit_signal": fit_signal,
            "recommended_outcome": assessment.recommended_outcome,
        },
    )
    return result.model_dump(exclude_none=True)
