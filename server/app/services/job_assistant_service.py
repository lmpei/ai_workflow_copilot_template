from collections.abc import Sequence
from typing import cast

from pydantic import ValidationError

from app.repositories import task_repository
from app.schemas.job import (
    JobArtifacts,
    JobAssistantResult,
    JobComparisonCandidate,
    JobEvidenceStatus,
    JobFinding,
    JobFitAssessment,
    JobFitSignal,
    JobReviewBrief,
    JobShortlistEntry,
    JobShortlistResult,
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
_JOB_EVIDENCE_STATUSES = {"grounded_matches", "documents_only", "no_documents"}
_JOB_FIT_SIGNALS = {
    "grounded_match_found",
    "role_requirements_grounded",
    "insufficient_grounding",
    "no_documents_available",
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


def _coerce_job_evidence_status(value: object) -> JobEvidenceStatus | None:
    if isinstance(value, str) and value in _JOB_EVIDENCE_STATUSES:
        return cast(JobEvidenceStatus, value)
    return None


def _coerce_job_fit_signal(value: object) -> JobFitSignal | None:
    if isinstance(value, str) and value in _JOB_FIT_SIGNALS:
        return cast(JobFitSignal, value)
    return None


def normalize_job_task_input(input_json: dict[str, object] | None) -> dict[str, object]:
    raw_input = input_json or {}
    if raw_input.get("target_role") is None and isinstance(raw_input.get("goal"), str):
        raise JobAssistantContractError(
            "Job task input must use target_role instead of goal",
        )

    payload_input = {
        "target_role": raw_input.get("target_role"),
        "candidate_label": raw_input.get("candidate_label"),
        "seniority": raw_input.get("seniority"),
        "must_have_skills": raw_input.get("must_have_skills", []),
        "preferred_skills": raw_input.get("preferred_skills", []),
        "hiring_context": raw_input.get("hiring_context"),
        "comparison_task_ids": raw_input.get("comparison_task_ids", []),
        "comparison_notes": raw_input.get("comparison_notes"),
    }
    try:
        payload = JobTaskInput.model_validate(payload_input)
    except ValidationError as error:
        raise JobAssistantContractError("Job 任务输入无效") from error

    normalized_payload: dict[str, object] = {}

    normalized_target_role = _normalize_optional_string(payload.target_role)
    if normalized_target_role:
        normalized_payload["target_role"] = normalized_target_role

    normalized_candidate_label = _normalize_optional_string(payload.candidate_label)
    if normalized_candidate_label:
        normalized_payload["candidate_label"] = normalized_candidate_label

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

    comparison_task_ids = _normalize_string_list(payload.comparison_task_ids)
    if comparison_task_ids:
        normalized_payload["comparison_task_ids"] = comparison_task_ids

    comparison_notes = _normalize_optional_string(payload.comparison_notes)
    if comparison_notes:
        normalized_payload["comparison_notes"] = comparison_notes

    return normalized_payload


def resolve_job_task_input(input_json: dict[str, object] | None) -> JobTaskInput:
    try:
        return JobTaskInput.model_validate(normalize_job_task_input(input_json))
    except ValidationError as error:
        raise JobAssistantContractError("Job 任务输入无效") from error


def _flatten_job_evidence_ref_ids(findings: Sequence[JobFinding]) -> list[str]:
    ref_ids: list[str] = []
    seen: set[str] = set()
    for finding in findings:
        for ref_id in finding.evidence_ref_ids:
            if ref_id in seen:
                continue
            seen.add(ref_id)
            ref_ids.append(ref_id)
    return ref_ids


def _extract_job_comparison_candidate(task_id: str) -> JobComparisonCandidate:
    task = task_repository.get_task(task_id)
    if task is None:
        raise JobAssistantContractError("未找到对比招聘任务")
    if get_scenario_task_module_type(task.task_type) != MODULE_TYPE_JOB:
        raise JobAssistantContractError("对比任务必须是已完成的 Job 评审任务")
    if task.task_type != "resume_match":
        raise JobAssistantContractError("对比任务必须是已完成的 Job resume_match 任务")
    if task.status != "done":
        raise JobAssistantContractError("对比招聘任务必须先完成后才能做短名单评审")

    result = task.output_json.get("result")
    if not isinstance(result, dict) or result.get("module_type") != MODULE_TYPE_JOB:
        raise JobAssistantContractError("对比招聘任务不包含结构化 Job 结果")

    title = result.get("title")
    summary = result.get("summary")
    if not isinstance(title, str) or not title.strip():
        raise JobAssistantContractError("对比招聘任务缺少 Job 标题")
    if not isinstance(summary, str) or not summary.strip():
        raise JobAssistantContractError("对比招聘任务缺少 Job 摘要")

    input_json = result.get("input")
    input_payload = input_json if isinstance(input_json, dict) else {}
    nested_comparison_ids = input_payload.get("comparison_task_ids")
    if isinstance(nested_comparison_ids, list) and len(nested_comparison_ids) > 0:
        raise JobAssistantContractError(
            "Comparison job task must be a single candidate review, not a prior shortlist",
        )
    assessment_json = result.get("assessment")
    assessment_payload = assessment_json if isinstance(assessment_json, dict) else {}
    findings_json = result.get("findings")
    findings_payload = findings_json if isinstance(findings_json, list) else []
    highlights_json = result.get("highlights")
    highlight_values = [
        item.strip()
        for item in highlights_json
        if isinstance(item, str) and item.strip()
    ] if isinstance(highlights_json, list) else []

    fit_signal = _coerce_job_fit_signal(assessment_payload.get("fit_signal"))
    evidence_status = _coerce_job_evidence_status(assessment_payload.get("evidence_status"))
    if fit_signal is None or evidence_status is None:
        raise JobAssistantContractError("对比招聘任务缺少结构化评估元数据")

    findings = [
        JobFinding.model_validate(finding)
        for finding in findings_payload
        if isinstance(finding, dict)
    ]
    candidate_label = _normalize_optional_string(cast(str | None, input_payload.get("candidate_label")))
    target_role = _normalize_optional_string(cast(str | None, input_payload.get("target_role")))

    return JobComparisonCandidate(
        task_id=task.id,
        task_type=cast(JobTaskType, task.task_type),
        candidate_label=candidate_label or f"Candidate {task.id[:8]}",
        title=title.strip(),
        summary=summary.strip(),
        target_role=target_role,
        seniority=_normalize_optional_string(cast(str | None, input_payload.get("seniority"))),
        fit_signal=fit_signal,
        evidence_status=evidence_status,
        recommended_outcome=_normalize_optional_string(
            cast(str | None, assessment_payload.get("recommended_outcome")),
        ),
        findings=findings,
        highlights=highlight_values,
        evidence_ref_ids=_flatten_job_evidence_ref_ids(findings),
    )


def resolve_job_comparison_candidates(
    *,
    workspace_id: str,
    job_input: JobTaskInput,
) -> list[JobComparisonCandidate]:
    comparison_candidates: list[JobComparisonCandidate] = []
    normalized_target_role = _normalize_optional_string(job_input.target_role)
    role_key = normalized_target_role.casefold() if normalized_target_role else None
    comparison_role_key: str | None = None

    for task_id in job_input.comparison_task_ids:
        candidate = _extract_job_comparison_candidate(task_id)
        task = task_repository.get_task(candidate.task_id)
        if task is None or task.workspace_id != workspace_id:
            raise JobAssistantContractError("当前工作区中未找到对比招聘任务")

        candidate_role = _normalize_optional_string(candidate.target_role)
        candidate_role_key = candidate_role.casefold() if candidate_role else None
        if comparison_role_key is None and candidate_role_key is not None:
            comparison_role_key = candidate_role_key
        elif comparison_role_key is not None and candidate_role_key is not None and candidate_role_key != comparison_role_key:
            raise JobAssistantContractError("对比招聘任务必须面向同一个岗位")
        if role_key is not None and candidate_role_key is not None and role_key != candidate_role_key:
            raise JobAssistantContractError("对比招聘任务必须与当前 target_role 一致")

        comparison_candidates.append(candidate)

    return comparison_candidates


def build_job_task_search_query(
    job_input: JobTaskInput,
    *,
    comparison_candidates: Sequence[JobComparisonCandidate] | None = None,
) -> str:
    query_parts: list[str] = []
    if job_input.target_role:
        query_parts.append(job_input.target_role)
    if job_input.candidate_label:
        query_parts.append(f"Candidate: {job_input.candidate_label}")
    if job_input.seniority:
        query_parts.append(f"Seniority: {job_input.seniority}")
    if job_input.must_have_skills:
        query_parts.append("Must-have skills: " + ", ".join(job_input.must_have_skills))
    if job_input.preferred_skills:
        query_parts.append("Preferred skills: " + ", ".join(job_input.preferred_skills))
    if job_input.hiring_context:
        query_parts.append(f"Hiring context: {job_input.hiring_context}")
    base_query = " | ".join(query_parts)

    if not comparison_candidates:
        return base_query

    comparison_parts = ["Compare these completed candidate reviews for the same hiring decision."]
    if job_input.comparison_notes:
        comparison_parts.append(f"Shortlist focus: {job_input.comparison_notes}")
    for candidate in comparison_candidates[:5]:
        comparison_parts.append(
            f"{candidate.candidate_label}: {candidate.summary} "
            f"(fit signal: {candidate.fit_signal}, evidence: {candidate.evidence_status})"
        )
    if base_query:
        comparison_parts.append(f"Current role context: {base_query}")
    return " ".join(comparison_parts)


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
    comparison_candidates: Sequence[JobComparisonCandidate],
) -> JobReviewBrief:
    comparison_role = next(
        (candidate.target_role for candidate in comparison_candidates if candidate.target_role),
        None,
    )
    return JobReviewBrief(
        role_summary=job_input.target_role or comparison_role or "General hiring review",
        candidate_label=job_input.candidate_label,
        seniority=job_input.seniority,
        must_have_skills=list(job_input.must_have_skills),
        preferred_skills=list(job_input.preferred_skills),
        hiring_context=job_input.hiring_context,
        evidence_status=evidence_status,
        comparison_task_count=len(comparison_candidates),
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


def _build_shortlist_entry(candidate: JobComparisonCandidate, rank: int) -> JobShortlistEntry:
    risks: list[str] = []
    interview_focus: list[str] = []

    if candidate.evidence_status != "grounded_matches":
        risks.append("Grounding is incomplete for this candidate review.")
    if candidate.fit_signal == "insufficient_grounding":
        risks.append("The candidate comparison should stay provisional until stronger evidence is indexed.")
    if candidate.fit_signal == "no_documents_available":
        risks.append("No indexed candidate materials were available for a grounded comparison.")

    if candidate.recommended_outcome == "advance_to_manual_review":
        recommendation = "Prioritize for shortlist discussion"
        rationale = "Grounded evidence exists and the prior review already recommended manual review."
        interview_focus.append("Validate the strongest grounded match signal against the actual role rubric.")
    elif candidate.recommended_outcome == "collect_more_hiring_signal":
        recommendation = "Keep in consideration but gather more signal"
        rationale = "Some materials exist, but the prior review could not support a confident grounded decision."
        interview_focus.append("Probe the candidate areas where the current materials are thin or ambiguous.")
    elif candidate.recommended_outcome == "gather_hiring_materials":
        recommendation = "Do not rank yet"
        rationale = "The prior review lacked indexed candidate evidence."
        interview_focus.append("Request or index the candidate materials needed for a grounded review.")
    else:
        recommendation = "Use as a supporting comparison signal"
        rationale = "The prior review adds context, but it does not yet justify a strong shortlist position on its own."
        interview_focus.append("Verify whether the candidate really matches the required role depth.")

    if not candidate.findings:
        interview_focus.append("Ask for concrete work examples because the review produced limited grounded findings.")
    else:
        interview_focus.append(f"Follow up on: {candidate.findings[0].summary}")

    return JobShortlistEntry(
        rank=rank,
        task_id=candidate.task_id,
        candidate_label=candidate.candidate_label,
        fit_signal=candidate.fit_signal,
        evidence_status=candidate.evidence_status,
        recommendation=recommendation,
        rationale=rationale,
        risks=risks,
        interview_focus=interview_focus,
        evidence_ref_ids=list(candidate.evidence_ref_ids),
    )


def _candidate_sort_key(candidate: JobComparisonCandidate) -> tuple[int, int]:
    fit_score = {
        "grounded_match_found": 4,
        "role_requirements_grounded": 3,
        "insufficient_grounding": 2,
        "no_documents_available": 1,
    }[candidate.fit_signal]
    evidence_score = {
        "grounded_matches": 3,
        "documents_only": 2,
        "no_documents": 1,
    }[candidate.evidence_status]
    return fit_score, evidence_score


def _build_shortlist(
    *,
    job_input: JobTaskInput,
    comparison_candidates: Sequence[JobComparisonCandidate],
) -> JobShortlistResult | None:
    if len(comparison_candidates) < 2:
        return None

    ranked_candidates = sorted(
        comparison_candidates,
        key=_candidate_sort_key,
        reverse=True,
    )
    shortlist_entries = [
        _build_shortlist_entry(candidate, rank=index + 1)
        for index, candidate in enumerate(ranked_candidates)
    ]

    shortlist_summary = (
        f"Compared {len(comparison_candidates)} completed candidate review task(s) for "
        f"{job_input.target_role or ranked_candidates[0].target_role or 'the current role'}."
    )
    shortlist_risks = [
        risk
        for entry in shortlist_entries
        for risk in entry.risks
    ]
    shortlist_focus = [
        focus
        for entry in shortlist_entries[:3]
        for focus in entry.interview_focus[:2]
    ]
    shortlist_gaps: list[str] = []
    if any(candidate.evidence_status != "grounded_matches" for candidate in comparison_candidates):
        shortlist_gaps.append("At least one candidate review is still weakly grounded.")
    if any(candidate.fit_signal == "no_documents_available" for candidate in comparison_candidates):
        shortlist_gaps.append("Some candidate reviews still lack indexed supporting materials.")

    return JobShortlistResult(
        comparison_task_ids=[candidate.task_id for candidate in comparison_candidates],
        comparison_notes=job_input.comparison_notes,
        shortlist_summary=shortlist_summary,
        entries=shortlist_entries,
        risks=shortlist_risks,
        interview_focus=shortlist_focus,
        gaps=shortlist_gaps,
    )


def build_job_task_result(
    *,
    task_type: JobTaskType,
    job_input: dict[str, object] | None,
    comparison_candidates: list[dict[str, object]] | None = None,
    documents: list[dict[str, object]],
    matches: list[dict[str, object]],
    tool_call_ids: list[str],
) -> dict[str, object]:
    validate_job_task_contract(
        workspace_module_type=MODULE_TYPE_JOB,
        task_type=task_type,
    )

    resolved_input = resolve_job_task_input(job_input)
    resolved_comparison_candidates = [
        JobComparisonCandidate.model_validate(candidate)
        for candidate in (comparison_candidates or [])
    ]
    document_models = [ToolDocumentSummary.model_validate(document) for document in documents]
    match_models = [SearchDocumentMatch.model_validate(match) for match in matches]
    evidence_status = _derive_evidence_status(
        has_documents=bool(document_models),
        has_matches=bool(match_models),
    )
    review_brief = _build_review_brief(
        job_input=resolved_input,
        evidence_status=evidence_status,
        comparison_candidates=resolved_comparison_candidates,
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
    shortlist = _build_shortlist(
        job_input=resolved_input,
        comparison_candidates=resolved_comparison_candidates,
    )

    if shortlist is not None:
        summary = shortlist.shortlist_summary
    elif evidence_status == "grounded_matches":
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
    if resolved_input.candidate_label:
        highlights.append(f"Candidate: {resolved_input.candidate_label}")
    if resolved_input.seniority:
        highlights.append(f"Seniority: {resolved_input.seniority}")
    if resolved_input.must_have_skills:
        highlights.append("Must-have skills: " + ", ".join(resolved_input.must_have_skills[:3]))
    if shortlist is not None:
        highlights.append(f"Shortlist candidates: {len(shortlist.entries)}")
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
        title="Candidate Comparison Shortlist" if shortlist is not None else _JOB_TASK_TITLES[task_type],
        input=resolved_input,
        review_brief=review_brief,
        findings=findings,
        gaps=gaps,
        assessment=assessment,
        comparison_candidates=resolved_comparison_candidates,
        shortlist=shortlist,
        open_questions=open_questions,
        next_steps=next_steps,
        summary=summary,
        highlights=highlights,
        evidence=evidence,
        artifacts=artifacts,
        metadata={
            "target_role": resolved_input.target_role,
            "candidate_label": resolved_input.candidate_label,
            "seniority": resolved_input.seniority,
            "must_have_skill_count": len(resolved_input.must_have_skills),
            "preferred_skill_count": len(resolved_input.preferred_skills),
            "comparison_task_count": len(resolved_comparison_candidates),
            "document_count": len(document_models),
            "match_count": len(match_models),
            "evidence_status": evidence_status,
            "fit_signal": fit_signal,
            "recommended_outcome": assessment.recommended_outcome,
            "shortlist_ready": shortlist is not None,
        },
    )
    return result.model_dump(exclude_none=True)
