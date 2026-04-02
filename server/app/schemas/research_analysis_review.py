from datetime import datetime

from pydantic import BaseModel


class ResearchAnalysisReviewRecord(BaseModel):
    run_id: str
    question: str
    status: str
    mode: str
    trace_id: str | None = None
    resumed_from_run_id: str | None = None
    degraded_reason: str | None = None
    run_memory_summary: str | None = None
    connector_id: str | None = None
    connector_consent_state: str | None = None
    external_context_used: bool | None = None
    external_match_count: int | None = None
    selected_external_resource_snapshot_id: str | None = None
    selected_external_resource_snapshot_title: str | None = None
    external_resource_snapshot_id: str | None = None
    external_resource_snapshot_title: str | None = None
    resource_selection_mode: str | None = None
    passed: bool
    issues: list[str]
    regression_baseline: dict[str, object]
    created_at: datetime
    completed_at: datetime | None = None


class ResearchAnalysisReviewResponse(BaseModel):
    baseline_version: str
    reviewed_count: int
    passing_count: int
    failing_count: int
    items: list[ResearchAnalysisReviewRecord]
