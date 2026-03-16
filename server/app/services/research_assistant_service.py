from pydantic import ValidationError

from app.schemas.research import (
    ResearchArtifacts,
    ResearchAssistantResult,
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


def normalize_research_task_input(input_json: dict[str, object] | None) -> dict[str, object]:
    try:
        payload = ResearchTaskInput.model_validate(input_json or {})
    except ValidationError as error:
        raise ResearchAssistantContractError("Invalid research task input") from error

    normalized_goal = payload.goal.strip() if isinstance(payload.goal, str) else None
    if normalized_goal:
        return {"goal": normalized_goal}
    return {}


def build_research_task_result(
    *,
    task_type: ResearchTaskType,
    goal: str,
    documents: list[dict[str, object]],
    matches: list[dict[str, object]],
    tool_call_ids: list[str],
) -> dict[str, object]:
    validate_research_task_contract(
        workspace_module_type=MODULE_TYPE_RESEARCH,
        task_type=task_type,
    )

    document_models = [ToolDocumentSummary.model_validate(document) for document in documents]
    match_models = [SearchDocumentMatch.model_validate(match) for match in matches]

    if not document_models:
        summary = "No workspace documents are available for analysis."
    elif not match_models:
        summary = (
            f"Reviewed {len(document_models)} workspace document(s), "
            "but no relevant indexed matches were found for the goal."
        )
    else:
        top_match = match_models[0]
        summary = (
            f"Reviewed {len(document_models)} workspace document(s). "
            f"Top match from {top_match.document_title} says: {top_match.snippet}"
        )

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
    else:
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
        summary=summary,
        highlights=highlights,
        evidence=evidence,
        artifacts=artifacts,
        metadata={
            "goal": goal,
            "document_count": len(document_models),
            "match_count": len(match_models),
        },
    )
    return result.model_dump()
