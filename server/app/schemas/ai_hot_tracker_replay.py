from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.ai_frontier_research import (
    AiHotTrackerChangeState,
    AiHotTrackerJudgmentFinding,
)


class AiHotTrackerReplayStepEvaluationResponse(BaseModel):
    label: str
    status: Literal["pass", "fail"]
    delta_change_state: AiHotTrackerChangeState
    should_notify: bool
    notify_reason: str | None = None
    ranked_item_ids: list[str] = Field(default_factory=list)
    cluster_titles: list[str] = Field(default_factory=list)
    findings: list[AiHotTrackerJudgmentFinding] = Field(default_factory=list)


class AiHotTrackerReplayCaseEvaluationResponse(BaseModel):
    case_id: str
    title: str
    description: str
    status: Literal["pass", "fail"]
    steps: list[AiHotTrackerReplayStepEvaluationResponse] = Field(default_factory=list)


class AiHotTrackerReplayEvaluationResponse(BaseModel):
    status: Literal["pass", "fail"]
    total_case_count: int = 0
    passed_case_count: int = 0
    failed_case_count: int = 0
    cases: list[AiHotTrackerReplayCaseEvaluationResponse] = Field(default_factory=list)
