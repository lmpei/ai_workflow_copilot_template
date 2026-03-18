from __future__ import annotations

from copy import deepcopy

from app.models.task import TASK_STATUS_DONE, Task
from app.repositories import research_asset_repository, task_repository, workspace_repository
from app.schemas.research_asset import (
    ResearchAssetCreate,
    ResearchAssetResponse,
    ResearchAssetRevisionResponse,
    ResearchAssetSummaryResponse,
)


class ResearchAssetAccessError(Exception):
    pass


class ResearchAssetValidationError(Exception):
    pass


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


def _build_asset_response(asset_id: str) -> ResearchAssetResponse:
    asset = research_asset_repository.get_research_asset(asset_id)
    if asset is None:
        raise ResearchAssetValidationError("Research asset not found")
    revisions = research_asset_repository.list_research_asset_revisions(asset_id)
    return ResearchAssetResponse(
        **ResearchAssetSummaryResponse.from_model(asset).model_dump(),
        revisions=[ResearchAssetRevisionResponse.from_model(revision) for revision in revisions],
    )


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
    return [ResearchAssetSummaryResponse.from_model(asset) for asset in assets]


def get_research_asset(
    *,
    asset_id: str,
    user_id: str,
) -> ResearchAssetResponse | None:
    asset = research_asset_repository.get_research_asset_for_user(asset_id, user_id)
    if asset is None:
        return None
    return _build_asset_response(asset.id)


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
