from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select

from app.core.database import session_scope
from app.models.research_asset import ResearchAsset
from app.models.research_asset_revision import ResearchAssetRevision
from app.models.workspace_member import WorkspaceMember


def get_research_asset(asset_id: str) -> ResearchAsset | None:
    with session_scope() as session:
        return session.get(ResearchAsset, asset_id)


def get_research_asset_for_user(asset_id: str, user_id: str) -> ResearchAsset | None:
    with session_scope() as session:
        statement = (
            select(ResearchAsset)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == ResearchAsset.workspace_id)
            .where(
                ResearchAsset.id == asset_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        return session.scalar(statement)


def list_workspace_research_assets(workspace_id: str, user_id: str) -> list[ResearchAsset]:
    with session_scope() as session:
        statement = (
            select(ResearchAsset)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == ResearchAsset.workspace_id)
            .where(
                ResearchAsset.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
            .order_by(ResearchAsset.updated_at.desc(), ResearchAsset.created_at.desc())
        )
        return list(session.scalars(statement))


def list_research_asset_revisions(asset_id: str) -> list[ResearchAssetRevision]:
    with session_scope() as session:
        statement = (
            select(ResearchAssetRevision)
            .where(ResearchAssetRevision.research_asset_id == asset_id)
            .order_by(ResearchAssetRevision.revision_number.desc(), ResearchAssetRevision.created_at.desc())
        )
        return list(session.scalars(statement))


def get_research_asset_revision_by_task_id(task_id: str) -> ResearchAssetRevision | None:
    with session_scope() as session:
        statement = select(ResearchAssetRevision).where(ResearchAssetRevision.task_id == task_id)
        return session.scalar(statement)


def get_research_asset_revision(revision_id: str) -> ResearchAssetRevision | None:
    with session_scope() as session:
        return session.get(ResearchAssetRevision, revision_id)


def create_research_asset(
    *,
    workspace_id: str,
    created_by: str,
    title: str,
    latest_task_id: str,
    latest_task_type: str,
    latest_input_json: dict[str, object],
    latest_result_json: dict[str, object],
    latest_summary: str,
    latest_report_headline: str | None,
) -> ResearchAsset:
    now = datetime.now(UTC)
    asset = ResearchAsset(
        id=str(uuid4()),
        workspace_id=workspace_id,
        created_by=created_by,
        title=title,
        latest_task_id=latest_task_id,
        latest_task_type=latest_task_type,
        latest_revision_number=1,
        latest_input_json=latest_input_json,
        latest_result_json=latest_result_json,
        latest_summary=latest_summary,
        latest_report_headline=latest_report_headline,
        created_at=now,
        updated_at=now,
    )
    with session_scope() as session:
        session.add(asset)
        session.flush()
        session.refresh(asset)
        return asset


def create_research_asset_revision(
    *,
    research_asset_id: str,
    task_id: str,
    task_type: str,
    revision_number: int,
    title: str,
    input_json: dict[str, object],
    result_json: dict[str, object],
    summary: str,
    report_headline: str | None,
) -> ResearchAssetRevision:
    revision = ResearchAssetRevision(
        id=str(uuid4()),
        research_asset_id=research_asset_id,
        task_id=task_id,
        task_type=task_type,
        revision_number=revision_number,
        title=title,
        input_json=input_json,
        result_json=result_json,
        summary=summary,
        report_headline=report_headline,
    )
    with session_scope() as session:
        session.add(revision)
        session.flush()
        session.refresh(revision)
        return revision


def update_research_asset_snapshot(
    asset_id: str,
    *,
    title: str | None = None,
    latest_task_id: str | None = None,
    latest_task_type: str | None = None,
    latest_revision_number: int | None = None,
    latest_input_json: dict[str, object] | None = None,
    latest_result_json: dict[str, object] | None = None,
    latest_summary: str | None = None,
    latest_report_headline: str | None = None,
) -> ResearchAsset | None:
    with session_scope() as session:
        asset = session.get(ResearchAsset, asset_id)
        if asset is None:
            return None

        if title is not None:
            asset.title = title
        if latest_task_id is not None:
            asset.latest_task_id = latest_task_id
        if latest_task_type is not None:
            asset.latest_task_type = latest_task_type
        if latest_revision_number is not None:
            asset.latest_revision_number = latest_revision_number
        if latest_input_json is not None:
            asset.latest_input_json = latest_input_json
        if latest_result_json is not None:
            asset.latest_result_json = latest_result_json
        if latest_summary is not None:
            asset.latest_summary = latest_summary
        asset.latest_report_headline = latest_report_headline
        asset.updated_at = datetime.now(UTC)

        session.add(asset)
        session.flush()
        session.refresh(asset)
        return asset
