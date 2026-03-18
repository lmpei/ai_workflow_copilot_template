from datetime import datetime

from pydantic import BaseModel, Field


class ResearchAssetCreate(BaseModel):
    task_id: str
    title: str | None = None


class ResearchAssetRevisionResponse(BaseModel):
    id: str
    research_asset_id: str
    task_id: str
    task_type: str
    revision_number: int
    title: str
    input_json: dict = Field(default_factory=dict)
    result_json: dict = Field(default_factory=dict)
    summary: str
    report_headline: str | None = None
    created_at: datetime

    @classmethod
    def from_model(cls, revision) -> "ResearchAssetRevisionResponse":
        return cls(
            id=revision.id,
            research_asset_id=revision.research_asset_id,
            task_id=revision.task_id,
            task_type=revision.task_type,
            revision_number=revision.revision_number,
            title=revision.title,
            input_json=revision.input_json,
            result_json=revision.result_json,
            summary=revision.summary,
            report_headline=revision.report_headline,
            created_at=revision.created_at,
        )


class ResearchAssetSummaryResponse(BaseModel):
    id: str
    workspace_id: str
    created_by: str
    title: str
    latest_task_id: str | None = None
    latest_task_type: str
    latest_revision_number: int
    latest_input_json: dict = Field(default_factory=dict)
    latest_result_json: dict = Field(default_factory=dict)
    latest_summary: str
    latest_report_headline: str | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, asset) -> "ResearchAssetSummaryResponse":
        return cls(
            id=asset.id,
            workspace_id=asset.workspace_id,
            created_by=asset.created_by,
            title=asset.title,
            latest_task_id=asset.latest_task_id,
            latest_task_type=asset.latest_task_type,
            latest_revision_number=asset.latest_revision_number,
            latest_input_json=asset.latest_input_json,
            latest_result_json=asset.latest_result_json,
            latest_summary=asset.latest_summary,
            latest_report_headline=asset.latest_report_headline,
            created_at=asset.created_at,
            updated_at=asset.updated_at,
        )


class ResearchAssetResponse(ResearchAssetSummaryResponse):
    revisions: list[ResearchAssetRevisionResponse] = Field(default_factory=list)
