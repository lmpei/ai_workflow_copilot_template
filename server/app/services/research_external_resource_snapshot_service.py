from app.connectors.research_external_context_connector import ResearchExternalContextEntry
from app.repositories import research_analysis_run_repository, workspace_repository
from app.schemas.research_external_resource_snapshot import ResearchExternalResourceSnapshotResponse


class ResearchExternalResourceSnapshotAccessError(Exception):
    pass


class ResearchExternalResourceSnapshotValidationError(Exception):
    pass


def _get_research_workspace_or_raise(*, workspace_id: str, user_id: str):
    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        raise ResearchExternalResourceSnapshotAccessError("Workspace not found")
    if workspace.module_type != "research":
        raise ResearchExternalResourceSnapshotValidationError(
            "Research external resource snapshots are only available in Research workspaces"
        )
    return workspace


def _serialize_matches(matches: list[ResearchExternalContextEntry]) -> list[dict[str, object]]:
    return [
        {
            "resource_id": match.context_id,
            "title": match.title,
            "source_label": match.source_label,
            "snippet": match.snippet,
        }
        for match in matches
    ]


def _build_snapshot_title(
    *,
    analysis_focus: str | None,
    search_query: str,
    matches: list[ResearchExternalContextEntry],
) -> str:
    if analysis_focus:
        return f"外部资源快照：{analysis_focus.strip()[:80]}"
    if matches:
        lead_title = matches[0].title.strip()
        if len(matches) == 1:
            return f"外部资源快照：{lead_title}"
        return f"外部资源快照：{lead_title} 等 {len(matches)} 条"
    return f"外部资源快照：{search_query.strip()[:80]}"


def create_research_external_resource_snapshot(
    *,
    workspace_id: str,
    conversation_id: str | None,
    created_by: str,
    connector_id: str,
    search_query: str,
    matches: list[ResearchExternalContextEntry],
    analysis_focus: str | None = None,
    source_run_id: str | None = None,
) -> ResearchExternalResourceSnapshotResponse:
    if not matches:
        raise ResearchExternalResourceSnapshotValidationError(
            "External resource snapshots require at least one approved external match"
        )

    snapshot = research_analysis_run_repository.create_research_external_resource_snapshot(
        workspace_id=workspace_id,
        conversation_id=conversation_id,
        created_by=created_by,
        connector_id=connector_id,
        source_run_id=source_run_id,
        title=_build_snapshot_title(
            analysis_focus=analysis_focus,
            search_query=search_query,
            matches=matches,
        ),
        analysis_focus=analysis_focus,
        search_query=search_query,
        resources_json=_serialize_matches(matches),
    )
    return ResearchExternalResourceSnapshotResponse.from_model(snapshot)


def list_workspace_research_external_resource_snapshots(
    *,
    workspace_id: str,
    user_id: str,
    limit: int = 8,
) -> list[ResearchExternalResourceSnapshotResponse]:
    _get_research_workspace_or_raise(workspace_id=workspace_id, user_id=user_id)
    normalized_limit = max(1, min(limit, 20))
    snapshots = research_analysis_run_repository.list_workspace_research_external_resource_snapshots(
        workspace_id=workspace_id,
        user_id=user_id,
        limit=normalized_limit,
    )
    return [ResearchExternalResourceSnapshotResponse.from_model(snapshot) for snapshot in snapshots]
