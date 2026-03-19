from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.research import ResearchBrief, ResearchTaskType


class ResearchAssetCreate(BaseModel):
    task_id: str
    title: str | None = None


class ResearchAssetComparisonRequest(BaseModel):
    left_asset_id: str
    right_asset_id: str
    left_revision_id: str | None = None
    right_revision_id: str | None = None


class ResearchAssetRevisionResponse(BaseModel):
    id: str
    research_asset_id: str
    task_id: str
    task_type: ResearchTaskType
    revision_number: int
    title: str
    brief: ResearchBrief
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
            brief=revision.brief,
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
    latest_task_type: ResearchTaskType
    latest_revision_number: int
    latest_brief: ResearchBrief
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
            latest_brief=asset.latest_brief,
            latest_input_json=asset.latest_input_json,
            latest_result_json=asset.latest_result_json,
            latest_summary=asset.latest_summary,
            latest_report_headline=asset.latest_report_headline,
            created_at=asset.created_at,
            updated_at=asset.updated_at,
        )


class ResearchAssetResponse(ResearchAssetSummaryResponse):
    revisions: list[ResearchAssetRevisionResponse] = Field(default_factory=list)


class ResearchAssetComparisonSideResponse(BaseModel):
    asset_id: str
    asset_title: str
    revision_id: str | None = None
    revision_number: int
    task_id: str | None = None
    task_type: ResearchTaskType
    brief: ResearchBrief
    summary: str
    report_headline: str | None = None
    open_questions: list[str] = Field(default_factory=list)
    findings_count: int
    evidence_count: int
    document_count: int
    match_count: int


class ResearchAssetComparisonDiffResponse(BaseModel):
    shared_focus_areas: list[str] = Field(default_factory=list)
    left_only_focus_areas: list[str] = Field(default_factory=list)
    right_only_focus_areas: list[str] = Field(default_factory=list)
    shared_key_questions: list[str] = Field(default_factory=list)
    left_only_key_questions: list[str] = Field(default_factory=list)
    right_only_key_questions: list[str] = Field(default_factory=list)
    shared_constraints: list[str] = Field(default_factory=list)
    left_only_constraints: list[str] = Field(default_factory=list)
    right_only_constraints: list[str] = Field(default_factory=list)
    left_only_open_questions: list[str] = Field(default_factory=list)
    right_only_open_questions: list[str] = Field(default_factory=list)
    summary_changed: bool
    report_headline_changed: bool
    finding_count_delta: int
    evidence_count_delta: int
    document_count_delta: int
    match_count_delta: int


class ResearchAssetComparisonResponse(BaseModel):
    left: ResearchAssetComparisonSideResponse
    right: ResearchAssetComparisonSideResponse
    diff: ResearchAssetComparisonDiffResponse
