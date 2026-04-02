from datetime import datetime

from pydantic import BaseModel


class ResearchAnalysisReviewRecord(BaseModel):
    run_id: str
    question: str
    status: str
    trace_id: str | None = None
    resumed_from_run_id: str | None = None
    degraded_reason: str | None = None
    run_memory_summary: str | None = None
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
