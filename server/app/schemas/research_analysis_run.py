from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.research_analysis_run import ResearchAnalysisRun
from app.schemas.chat import ChatMode, ChatToolStep, SourceReference

ResearchAnalysisRunStatus = Literal["pending", "running", "completed", "degraded", "failed"]


class ResearchAnalysisRunCreate(BaseModel):
    question: str
    conversation_id: str | None = None
    mode: ChatMode = "research_tool_assisted"


class ResearchAnalysisRunMemory(BaseModel):
    memory_version: int = 1
    summary: str
    evidence_state: str
    recommended_next_step: str
    source_titles: list[str] = Field(default_factory=list)


class ResearchAnalysisRunResponse(BaseModel):
    id: str
    workspace_id: str
    conversation_id: str
    created_by: str
    status: ResearchAnalysisRunStatus
    question: str
    mode: ChatMode
    resumed_from_run_id: str | None = None
    answer: str | None = None
    trace_id: str | None = None
    sources: list[SourceReference]
    tool_steps: list[ChatToolStep]
    run_memory: ResearchAnalysisRunMemory | None = None
    analysis_focus: str | None = None
    search_query: str | None = None
    degraded_reason: str | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    updated_at: datetime

    @classmethod
    def from_model(cls, run: ResearchAnalysisRun) -> "ResearchAnalysisRunResponse":
        return cls(
            id=run.id,
            workspace_id=run.workspace_id,
            conversation_id=run.conversation_id,
            created_by=run.created_by,
            status=run.status,
            question=run.question,
            mode=run.mode,  # type: ignore[arg-type]
            resumed_from_run_id=run.resumed_from_run_id,
            answer=run.answer,
            trace_id=run.trace_id,
            sources=[SourceReference.model_validate(item) for item in run.sources_json],
            tool_steps=[ChatToolStep.model_validate(item) for item in run.tool_steps_json],
            run_memory=ResearchAnalysisRunMemory.model_validate(run.run_memory_json) if run.run_memory_json else None,
            analysis_focus=run.analysis_focus,
            search_query=run.search_query,
            degraded_reason=run.degraded_reason,
            error_message=run.error_message,
            created_at=run.created_at,
            started_at=run.started_at,
            completed_at=run.completed_at,
            updated_at=run.updated_at,
        )
