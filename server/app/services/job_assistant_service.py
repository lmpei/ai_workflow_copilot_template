from pydantic import ValidationError

from app.schemas.job import JobArtifacts, JobAssistantResult, JobTaskInput, JobTaskType
from app.schemas.scenario import (
    MODULE_TYPE_JOB,
    ScenarioEvidenceItem,
    get_scenario_task_module_type,
    get_supported_scenario_task_types,
)
from app.schemas.tool import SearchDocumentMatch, ToolDocumentSummary

_JOB_TASK_TITLES = {
    "jd_summary": "Job Description Summary",
    "resume_match": "Resume Match Summary",
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


def normalize_job_task_input(input_json: dict[str, object] | None) -> dict[str, object]:
    raw_input = input_json or {}
    if raw_input.get("target_role") is None and isinstance(raw_input.get("goal"), str):
        raise JobAssistantContractError(
            "Job task input must use target_role instead of goal",
        )

    payload_input = {
        "target_role": raw_input.get("target_role"),
    }
    try:
        payload = JobTaskInput.model_validate(payload_input)
    except ValidationError as error:
        raise JobAssistantContractError("Invalid job task input") from error

    normalized_target_role = (
        payload.target_role.strip() if isinstance(payload.target_role, str) else None
    )
    if normalized_target_role:
        return {"target_role": normalized_target_role}
    return {}


def _build_fit_signal(*, has_documents: bool, has_matches: bool) -> str:
    if has_matches:
        return "grounded_match_found"
    if has_documents:
        return "insufficient_grounding"
    return "no_documents_available"


def _build_recommended_next_step(
    *,
    task_type: JobTaskType,
    has_documents: bool,
    has_matches: bool,
) -> str:
    if has_matches:
        if task_type == "resume_match":
            return (
                "Review the top grounded match evidence and decide "
                "whether the candidate should advance."
            )
        return (
            "Use the grounded highlights to refine the final job "
            "requirements and screening criteria."
        )
    if has_documents:
        return (
            "Add a clearer target role or upload more structured "
            "hiring materials before rerunning this task."
        )
    return "Upload job descriptions or candidate materials to produce a grounded job result."


def build_job_task_result(
    *,
    task_type: JobTaskType,
    target_role: str,
    documents: list[dict[str, object]],
    matches: list[dict[str, object]],
    tool_call_ids: list[str],
) -> dict[str, object]:
    validate_job_task_contract(
        workspace_module_type=MODULE_TYPE_JOB,
        task_type=task_type,
    )

    document_models = [ToolDocumentSummary.model_validate(document) for document in documents]
    match_models = [SearchDocumentMatch.model_validate(match) for match in matches]
    fit_signal = _build_fit_signal(
        has_documents=bool(document_models),
        has_matches=bool(match_models),
    )
    recommended_next_step = _build_recommended_next_step(
        task_type=task_type,
        has_documents=bool(document_models),
        has_matches=bool(match_models),
    )

    if not document_models:
        summary = "No job documents are available for this workspace."
    elif not match_models:
        summary = (
            f"Reviewed {len(document_models)} job document(s), "
            "but no grounded match was found for the current role focus."
        )
    else:
        top_match = match_models[0]
        summary = (
            f"Reviewed {len(document_models)} job document(s). "
            f"Top grounded signal from {top_match.document_title}: {top_match.snippet}"
        )

    if match_models:
        highlights = [
            f"Role focus: {target_role}" if target_role else "Role focus: general job review",
            *[f"{match.document_title}: {match.snippet}" for match in match_models[:2]],
        ]
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
        highlights = [
            f"Role focus: {target_role}" if target_role else "Role focus: general job review",
        ]
        if document_models:
            highlights.extend(
                f"Available document: {document.title} ({document.status})"
                for document in document_models[:2]
            )
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
        fit_signal=fit_signal,
        recommended_next_step=recommended_next_step,
    )
    result = JobAssistantResult(
        task_type=task_type,
        title=_JOB_TASK_TITLES[task_type],
        summary=summary,
        highlights=highlights,
        evidence=evidence,
        artifacts=artifacts,
        metadata={
            "target_role": target_role,
            "document_count": len(document_models),
            "match_count": len(match_models),
        },
    )
    return result.model_dump()