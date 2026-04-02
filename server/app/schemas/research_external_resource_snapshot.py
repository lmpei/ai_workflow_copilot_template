from datetime import datetime

from pydantic import BaseModel

from app.models.research_external_resource_snapshot import ResearchExternalResourceSnapshot


class ResearchExternalResourceSnapshotItem(BaseModel):
    resource_id: str
    title: str
    source_label: str
    snippet: str


class ResearchExternalResourceSnapshotResponse(BaseModel):
    id: str
    workspace_id: str
    conversation_id: str | None = None
    created_by: str
    connector_id: str
    source_run_id: str | None = None
    title: str
    analysis_focus: str | None = None
    search_query: str
    resource_count: int
    resources: list[ResearchExternalResourceSnapshotItem]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(
        cls,
        snapshot: ResearchExternalResourceSnapshot,
    ) -> "ResearchExternalResourceSnapshotResponse":
        return cls(
            id=snapshot.id,
            workspace_id=snapshot.workspace_id,
            conversation_id=snapshot.conversation_id,
            created_by=snapshot.created_by,
            connector_id=snapshot.connector_id,
            source_run_id=snapshot.source_run_id,
            title=snapshot.title,
            analysis_focus=snapshot.analysis_focus,
            search_query=snapshot.search_query,
            resource_count=snapshot.resource_count,
            resources=[
                ResearchExternalResourceSnapshotItem.model_validate(item)
                for item in snapshot.resources_json
            ],
            created_at=snapshot.created_at,
            updated_at=snapshot.updated_at,
        )
