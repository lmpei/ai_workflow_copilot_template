from __future__ import annotations

from copy import deepcopy

from app.models.task import TASK_STATUS_DONE, Task
from app.repositories import research_asset_repository, task_repository, workspace_repository
from app.schemas.research import ResearchBrief, ResearchTaskType
from app.schemas.research_asset import (
    ResearchAssetComparisonDiffResponse,
    ResearchAssetComparisonRequest,
    ResearchAssetComparisonResponse,
    ResearchAssetComparisonSideResponse,
    ResearchAssetCreate,
    ResearchAssetResponse,
    ResearchAssetRevisionResponse,
    ResearchAssetSummaryResponse,
)
from app.services.research_assistant_service import ResearchAssistantContractError, resolve_research_task_input


class ResearchAssetAccessError(Exception):
    pass


class ResearchAssetValidationError(Exception):
    pass


def _coerce_research_task_type(value: object) -> ResearchTaskType:
    if value in {"research_summary", "workspace_report"}:
        return value
    raise ResearchAssetValidationError("Research asset contains an unsupported task type")


def _normalize_string_list(values: object) -> list[str]:
    if not isinstance(values, list):
        return []

    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        item = value.strip()
        if not item or item in seen:
            continue
        normalized.append(item)
        seen.add(item)
    return normalized


def _build_research_brief(
    *,
    task_type: object,
    input_json: object,
) -> ResearchBrief:
    task_type_value = _coerce_research_task_type(task_type)
    input_payload = input_json if isinstance(input_json, dict) else {}

    try:
        normalized_input = resolve_research_task_input(
            task_type=task_type_value,
            input_json=input_payload,
        )
        return ResearchBrief(
            goal=normalized_input.goal,
            focus_areas=list(normalized_input.focus_areas),
            key_questions=list(normalized_input.key_questions),
            constraints=list(normalized_input.constraints),
            deliverable=normalized_input.deliverable,
            requested_sections=list(normalized_input.requested_sections),
            continuation_notes=normalized_input.continuation_notes,
        )
    except ResearchAssistantContractError:
        return ResearchBrief(
            goal=input_payload.get("goal") if isinstance(input_payload.get("goal"), str) else None,
            focus_areas=_normalize_string_list(input_payload.get("focus_areas")),
            key_questions=_normalize_string_list(input_payload.get("key_questions")),
            constraints=_normalize_string_list(input_payload.get("constraints")),
            deliverable=input_payload.get("deliverable")
            if input_payload.get("deliverable") in {"brief", "report"}
            else None,
            requested_sections=_normalize_string_list(input_payload.get("requested_sections")),
            continuation_notes=input_payload.get("continuation_notes")
            if isinstance(input_payload.get("continuation_notes"), str)
            else None,
        )


def _resolve_brief_source(
    *,
    input_json: object,
    result_json: object,
) -> object:
    if isinstance(result_json, dict):
        result_input = result_json.get("input")
        if isinstance(result_input, dict):
            return result_input
    return input_json


def _extract_research_result(task: Task) -> dict[str, object]:
    if task.task_type not in {"research_summary", "workspace_report"}:
        raise ResearchAssetValidationError("Task must be a completed Research task")
    if task.status != TASK_STATUS_DONE:
        raise ResearchAssetValidationError("Research asset source task must be completed")

    result = task.output_json.get("result")
    if not isinstance(result, dict) or result.get("module_type") != "research":
        raise ResearchAssetValidationError("Task does not contain a structured Research result")
    return result


def _extract_report_headline(result: dict[str, object]) -> str | None:
    report = result.get("report")
    if not isinstance(report, dict):
        return None
    headline = report.get("headline")
    if isinstance(headline, str) and headline.strip():
        return headline.strip()
    return None


def _extract_open_questions(result_json: dict[str, object]) -> list[str]:
    sections = result_json.get("sections")
    if isinstance(sections, dict):
        open_questions = _normalize_string_list(sections.get("open_questions"))
        if open_questions:
            return open_questions

    report = result_json.get("report")
    if isinstance(report, dict):
        return _normalize_string_list(report.get("open_questions"))

    return []


def _extract_findings_count(result_json: dict[str, object]) -> int:
    sections = result_json.get("sections")
    if not isinstance(sections, dict):
        return 0
    findings = sections.get("findings")
    if not isinstance(findings, list):
        return 0
    return len(findings)


def _extract_evidence_count(result_json: dict[str, object]) -> int:
    evidence = result_json.get("evidence")
    if not isinstance(evidence, list):
        return 0
    return len(evidence)


def _extract_artifact_count(result_json: dict[str, object], key: str) -> int:
    artifacts = result_json.get("artifacts")
    if not isinstance(artifacts, dict):
        return 0
    value = artifacts.get(key)
    if isinstance(value, int):
        return value
    return 0


def _ordered_shared(left: list[str], right: list[str]) -> list[str]:
    right_set = set(right)
    return [item for item in left if item in right_set]


def _ordered_only(left: list[str], right: list[str]) -> list[str]:
    right_set = set(right)
    return [item for item in left if item not in right_set]


def _derive_asset_title(
    *,
    task: Task,
    result: dict[str, object],
    requested_title: str | None,
) -> str:
    if isinstance(requested_title, str) and requested_title.strip():
        return requested_title.strip()

    report_headline = _extract_report_headline(result)
    if report_headline:
        return report_headline

    input_json = result.get("input")
    if isinstance(input_json, dict):
        goal = input_json.get("goal")
        if isinstance(goal, str) and goal.strip():
            return goal.strip()

    title = result.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()

    return f"Research asset {task.id}"


def _build_asset_result_metadata(
    *,
    asset_id: str,
    revision_id: str,
    revision_number: int,
) -> dict[str, object]:
    return {
        "research_asset": {
            "asset_id": asset_id,
            "revision_id": revision_id,
            "revision_number": revision_number,
        }
    }


def _write_asset_metadata_to_task(
    *,
    task: Task,
    asset_id: str,
    revision_id: str,
    revision_number: int,
) -> None:
    output_json = deepcopy(task.output_json)
    result = output_json.get("result")
    if not isinstance(result, dict):
        return

    metadata = result.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
        result["metadata"] = metadata

    metadata.update(
        _build_asset_result_metadata(
            asset_id=asset_id,
            revision_id=revision_id,
            revision_number=revision_number,
        )
    )
    task_repository.update_task_status(
        task.id,
        next_status=task.status,
        output_json=output_json,
    )


def _enrich_asset(asset) -> ResearchAssetSummaryResponse:
    latest_task_type = _coerce_research_task_type(asset.latest_task_type)
    return ResearchAssetSummaryResponse(
        id=asset.id,
        workspace_id=asset.workspace_id,
        created_by=asset.created_by,
        title=asset.title,
        latest_task_id=asset.latest_task_id,
        latest_task_type=latest_task_type,
        latest_revision_number=asset.latest_revision_number,
        latest_brief=_build_research_brief(
            task_type=latest_task_type,
            input_json=_resolve_brief_source(
                input_json=asset.latest_input_json,
                result_json=asset.latest_result_json,
            ),
        ),
        latest_input_json=asset.latest_input_json,
        latest_result_json=asset.latest_result_json,
        latest_summary=asset.latest_summary,
        latest_report_headline=asset.latest_report_headline,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


def _enrich_revision(revision) -> ResearchAssetRevisionResponse:
    task_type = _coerce_research_task_type(revision.task_type)
    return ResearchAssetRevisionResponse(
        id=revision.id,
        research_asset_id=revision.research_asset_id,
        task_id=revision.task_id,
        task_type=task_type,
        revision_number=revision.revision_number,
        title=revision.title,
        brief=_build_research_brief(
            task_type=task_type,
            input_json=_resolve_brief_source(
                input_json=revision.input_json,
                result_json=revision.result_json,
            ),
        ),
        input_json=revision.input_json,
        result_json=revision.result_json,
        summary=revision.summary,
        report_headline=revision.report_headline,
        created_at=revision.created_at,
    )


def _build_asset_response(asset_id: str) -> ResearchAssetResponse:
    asset = research_asset_repository.get_research_asset(asset_id)
    if asset is None:
        raise ResearchAssetValidationError("Research asset not found")
    revisions = research_asset_repository.list_research_asset_revisions(asset_id)
    enriched_asset = _enrich_asset(asset)
    return ResearchAssetResponse(
        **enriched_asset.model_dump(),
        revisions=[_enrich_revision(revision) for revision in revisions],
    )


def _build_comparison_side(
    *,
    asset,
    revision,
) -> ResearchAssetComparisonSideResponse:
    enriched_revision = _enrich_revision(revision)
    result_json = enriched_revision.result_json if isinstance(enriched_revision.result_json, dict) else {}
    return ResearchAssetComparisonSideResponse(
        asset_id=asset.id,
        asset_title=asset.title,
        revision_id=enriched_revision.id,
        revision_number=enriched_revision.revision_number,
        task_id=enriched_revision.task_id,
        task_type=enriched_revision.task_type,
        brief=enriched_revision.brief,
        summary=enriched_revision.summary,
        report_headline=enriched_revision.report_headline,
        open_questions=_extract_open_questions(result_json),
        findings_count=_extract_findings_count(result_json),
        evidence_count=_extract_evidence_count(result_json),
        document_count=_extract_artifact_count(result_json, "document_count"),
        match_count=_extract_artifact_count(result_json, "match_count"),
    )


def _build_comparison_diff(
    *,
    left: ResearchAssetComparisonSideResponse,
    right: ResearchAssetComparisonSideResponse,
) -> ResearchAssetComparisonDiffResponse:
    return ResearchAssetComparisonDiffResponse(
        shared_focus_areas=_ordered_shared(left.brief.focus_areas, right.brief.focus_areas),
        left_only_focus_areas=_ordered_only(left.brief.focus_areas, right.brief.focus_areas),
        right_only_focus_areas=_ordered_only(right.brief.focus_areas, left.brief.focus_areas),
        shared_key_questions=_ordered_shared(left.brief.key_questions, right.brief.key_questions),
        left_only_key_questions=_ordered_only(left.brief.key_questions, right.brief.key_questions),
        right_only_key_questions=_ordered_only(right.brief.key_questions, left.brief.key_questions),
        shared_constraints=_ordered_shared(left.brief.constraints, right.brief.constraints),
        left_only_constraints=_ordered_only(left.brief.constraints, right.brief.constraints),
        right_only_constraints=_ordered_only(right.brief.constraints, left.brief.constraints),
        left_only_open_questions=_ordered_only(left.open_questions, right.open_questions),
        right_only_open_questions=_ordered_only(right.open_questions, left.open_questions),
        summary_changed=left.summary != right.summary,
        report_headline_changed=left.report_headline != right.report_headline,
        finding_count_delta=right.findings_count - left.findings_count,
        evidence_count_delta=right.evidence_count - left.evidence_count,
        document_count_delta=right.document_count - left.document_count,
        match_count_delta=right.match_count - left.match_count,
    )


def _get_asset_for_user_or_raise(*, asset_id: str, user_id: str):
    asset = research_asset_repository.get_research_asset_for_user(asset_id, user_id)
    if asset is None:
        raise ResearchAssetAccessError("Research asset not found")
    return asset


def _get_revision_for_asset_or_raise(*, asset, revision_id: str | None):
    if revision_id:
        revision = research_asset_repository.get_research_asset_revision(revision_id)
        if revision is None:
            raise ResearchAssetValidationError("Research asset revision not found")
        if revision.research_asset_id != asset.id:
            raise ResearchAssetValidationError("Revision does not belong to the requested Research asset")
        return revision

    revisions = research_asset_repository.list_research_asset_revisions(asset.id)
    if not revisions:
        raise ResearchAssetValidationError("Research asset has no revisions to compare")
    return revisions[0]


def create_research_asset_from_task(
    *,
    workspace_id: str,
    user_id: str,
    payload: ResearchAssetCreate,
) -> ResearchAssetResponse:
    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        raise ResearchAssetAccessError("Workspace not found")

    task = task_repository.get_task_for_user(payload.task_id, user_id)
    if task is None or task.workspace_id != workspace_id:
        raise ResearchAssetAccessError("Research task not found in this workspace")

    result = _extract_research_result(task)
    existing_revision = research_asset_repository.get_research_asset_revision_by_task_id(task.id)
    if existing_revision is not None:
        return _build_asset_response(existing_revision.research_asset_id)

    asset = research_asset_repository.create_research_asset(
        workspace_id=workspace_id,
        created_by=user_id,
        title=_derive_asset_title(task=task, result=result, requested_title=payload.title),
        latest_task_id=task.id,
        latest_task_type=task.task_type,
        latest_input_json=deepcopy(task.input_json),
        latest_result_json=deepcopy(result),
        latest_summary=str(result.get("summary", "")),
        latest_report_headline=_extract_report_headline(result),
    )
    revision = research_asset_repository.create_research_asset_revision(
        research_asset_id=asset.id,
        task_id=task.id,
        task_type=task.task_type,
        revision_number=1,
        title=asset.title,
        input_json=deepcopy(task.input_json),
        result_json=deepcopy(result),
        summary=str(result.get("summary", "")),
        report_headline=_extract_report_headline(result),
    )
    _write_asset_metadata_to_task(
        task=task,
        asset_id=asset.id,
        revision_id=revision.id,
        revision_number=revision.revision_number,
    )
    return _build_asset_response(asset.id)


def list_workspace_research_assets(
    *,
    workspace_id: str,
    user_id: str,
) -> list[ResearchAssetSummaryResponse]:
    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        raise ResearchAssetAccessError("Workspace not found")

    assets = research_asset_repository.list_workspace_research_assets(workspace_id, user_id)
    return [_enrich_asset(asset) for asset in assets]


def get_research_asset(
    *,
    asset_id: str,
    user_id: str,
) -> ResearchAssetResponse | None:
    asset = research_asset_repository.get_research_asset_for_user(asset_id, user_id)
    if asset is None:
        return None
    return _build_asset_response(asset.id)


def compare_research_assets(
    *,
    user_id: str,
    payload: ResearchAssetComparisonRequest,
) -> ResearchAssetComparisonResponse:
    left_asset = _get_asset_for_user_or_raise(asset_id=payload.left_asset_id, user_id=user_id)
    right_asset = _get_asset_for_user_or_raise(asset_id=payload.right_asset_id, user_id=user_id)

    left_revision = _get_revision_for_asset_or_raise(asset=left_asset, revision_id=payload.left_revision_id)
    right_revision = _get_revision_for_asset_or_raise(asset=right_asset, revision_id=payload.right_revision_id)

    left_side = _build_comparison_side(asset=left_asset, revision=left_revision)
    right_side = _build_comparison_side(asset=right_asset, revision=right_revision)
    return ResearchAssetComparisonResponse(
        left=left_side,
        right=right_side,
        diff=_build_comparison_diff(left=left_side, right=right_side),
    )


def sync_research_asset_from_task(
    *,
    research_asset_id: str,
    task: Task,
    result_json: dict[str, object],
) -> dict[str, object]:
    asset = research_asset_repository.get_research_asset(research_asset_id)
    if asset is None:
        raise ResearchAssetValidationError("Research asset not found")
    if asset.workspace_id != task.workspace_id:
        raise ResearchAssetValidationError("Research asset does not belong to this workspace")

    existing_revision = research_asset_repository.get_research_asset_revision_by_task_id(task.id)
    if existing_revision is not None:
        _write_asset_metadata_to_task(
            task=task,
            asset_id=asset.id,
            revision_id=existing_revision.id,
            revision_number=existing_revision.revision_number,
        )
        return _build_asset_result_metadata(
            asset_id=asset.id,
            revision_id=existing_revision.id,
            revision_number=existing_revision.revision_number,
        )

    revision_number = asset.latest_revision_number + 1
    revision = research_asset_repository.create_research_asset_revision(
        research_asset_id=asset.id,
        task_id=task.id,
        task_type=task.task_type,
        revision_number=revision_number,
        title=asset.title,
        input_json=deepcopy(task.input_json),
        result_json=deepcopy(result_json),
        summary=str(result_json.get("summary", "")),
        report_headline=_extract_report_headline(result_json),
    )
    research_asset_repository.update_research_asset_snapshot(
        asset.id,
        latest_task_id=task.id,
        latest_task_type=task.task_type,
        latest_revision_number=revision_number,
        latest_input_json=deepcopy(task.input_json),
        latest_result_json=deepcopy(result_json),
        latest_summary=str(result_json.get("summary", "")),
        latest_report_headline=_extract_report_headline(result_json),
    )
    return _build_asset_result_metadata(
        asset_id=asset.id,
        revision_id=revision.id,
        revision_number=revision.revision_number,
    )
