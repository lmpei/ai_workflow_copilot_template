from pydantic import ValidationError

from app.schemas.scenario import (
    MODULE_TYPE_SUPPORT,
    ScenarioEvidenceItem,
    get_supported_scenario_task_types,
)
from app.schemas.support import (
    SupportArtifacts,
    SupportCopilotResult,
    SupportTaskInput,
    SupportTaskType,
)
from app.schemas.tool import SearchDocumentMatch, ToolDocumentSummary

SUPPORTED_SUPPORT_TASK_TYPES = {
    "ticket_summary",
    "reply_draft",
}

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
    if task_type not in SUPPORTED_SUPPORT_TASK_TYPES:
        raise SupportCopilotContractError(
            f"Support Copilot does not support task type: {task_type}",
        )
    if workspace_module_type != MODULE_TYPE_SUPPORT:
        raise SupportCopilotContractError(
            f"Support Copilot requires workspace module {MODULE_TYPE_SUPPORT}",
        )



def normalize_support_task_input(input_json: dict[str, object] | None) -> dict[str, object]:
    raw_input = input_json or {}
    payload_input = {
        "customer_issue": raw_input.get("customer_issue") or raw_input.get("goal"),
    }
    try:
        payload = SupportTaskInput.model_validate(payload_input)
    except ValidationError as error:
        raise SupportCopilotContractError("Invalid support task input") from error

    normalized_issue = (
        payload.customer_issue.strip() if isinstance(payload.customer_issue, str) else None
    )
    if normalized_issue:
        return {"customer_issue": normalized_issue}
    return {}



def _build_reply_draft(
    *,
    customer_issue: str,
    match_models: list[SearchDocumentMatch],
    has_documents: bool,
) -> str:
    if match_models:
        top_match = match_models[0]
        return (
            "Thanks for reaching out. Based on our current support knowledge base, "
            f"the most relevant guidance is: {top_match.snippet}"
        )
    if has_documents:
        return (
            "Thanks for reaching out. We reviewed the current support knowledge base, "
            "but we could not find a confident grounded answer yet. "
            "This case should be reviewed manually."
        )
    return (
        "Thanks for reaching out. This workspace does not have indexed support knowledge yet, "
        "so this reply should be reviewed and completed manually."
    )



def build_support_task_result(
    *,
    task_type: SupportTaskType,
    customer_issue: str,
    documents: list[dict[str, object]],
    matches: list[dict[str, object]],
    tool_call_ids: list[str],
) -> dict[str, object]:
    validate_support_task_contract(
        workspace_module_type=MODULE_TYPE_SUPPORT,
        task_type=task_type,
    )

    document_models = [ToolDocumentSummary.model_validate(document) for document in documents]
    match_models = [SearchDocumentMatch.model_validate(match) for match in matches]
    draft_reply = (
        _build_reply_draft(
            customer_issue=customer_issue,
            match_models=match_models,
            has_documents=bool(document_models),
        )
        if task_type == "reply_draft"
        else None
    )

    if not document_models:
        summary = "No support knowledge documents are available for this workspace."
    elif not match_models:
        summary = (
            f"Reviewed {len(document_models)} support knowledge document(s), "
            "but no grounded match was found for the current issue."
        )
    else:
        top_match = match_models[0]
        summary = (
            f"Reviewed {len(document_models)} support knowledge document(s). "
            f"Top grounded guidance from {top_match.document_title}: {top_match.snippet}"
        )

    if match_models:
        highlights = [
            f"Issue: {customer_issue}",
            *[f"{match.document_title}: {match.snippet}" for match in match_models[:2]],
        ]
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
        highlights = [f"Issue: {customer_issue}"]
        if document_models:
            highlights.extend(
                f"Knowledge source available: {document.title} ({document.status})"
                for document in document_models[:2]
            )
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
        draft_reply=draft_reply,
    )
    result = SupportCopilotResult(
        task_type=task_type,
        title=_SUPPORT_TASK_TITLES[task_type],
        summary=summary,
        highlights=highlights,
        evidence=evidence,
        artifacts=artifacts,
        metadata={
            "customer_issue": customer_issue,
            "document_count": len(document_models),
            "match_count": len(match_models),
        },
    )
    return result.model_dump()
