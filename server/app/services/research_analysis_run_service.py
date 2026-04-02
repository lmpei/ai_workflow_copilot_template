from datetime import UTC, datetime

from arq import create_pool

from app.core.config import get_settings
from app.core.queue import build_redis_settings
from app.repositories import conversation_repository, research_analysis_run_repository, workspace_repository
from app.schemas.research_analysis_run import ResearchAnalysisRunCreate, ResearchAnalysisRunResponse
from app.services.research_tool_assisted_chat_service import run_tool_assisted_research_chat
from app.services.retrieval_generation_service import ChatProcessingError
from app.services.trace_service import record_chat_trace

RESEARCH_ANALYSIS_RUN_JOB_NAME = "run_research_analysis_run"


class ResearchAnalysisRunAccessError(Exception):
    pass


class ResearchAnalysisRunValidationError(Exception):
    pass


class ResearchAnalysisRunQueueError(Exception):
    pass


class ResearchAnalysisRunExecutionError(Exception):
    pass


def _build_conversation_title(question: str) -> str:
    title = question.strip() or "New research analysis"
    return title[:255]


def _get_research_workspace_or_raise(*, workspace_id: str, user_id: str):
    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        raise ResearchAnalysisRunAccessError("Workspace not found")
    if workspace.module_type != "research":
        raise ResearchAnalysisRunValidationError("Background analysis runs are only available in Research workspaces")
    return workspace


def _ensure_conversation(
    *,
    workspace_id: str,
    user_id: str,
    question: str,
    conversation_id: str | None,
):
    if conversation_id is None:
        return conversation_repository.create_conversation(
            workspace_id=workspace_id,
            user_id=user_id,
            title=_build_conversation_title(question),
        )

    conversation = conversation_repository.get_conversation(
        conversation_id=conversation_id,
        workspace_id=workspace_id,
        user_id=user_id,
    )
    if conversation is None:
        raise ResearchAnalysisRunAccessError("Conversation not found")
    return conversation


async def enqueue_research_analysis_run_execution(run_id: str) -> str:
    redis = await create_pool(build_redis_settings())
    job = await redis.enqueue_job(
        RESEARCH_ANALYSIS_RUN_JOB_NAME,
        run_id,
        _queue_name=get_settings().task_queue_name,
    )
    close = getattr(redis, "aclose", None)
    if callable(close):
        await close()
    if job is None:
        raise ResearchAnalysisRunQueueError("Failed to enqueue the research analysis run")
    return str(job.job_id)


async def create_research_analysis_run(
    *,
    workspace_id: str,
    user_id: str,
    payload: ResearchAnalysisRunCreate,
) -> ResearchAnalysisRunResponse:
    _get_research_workspace_or_raise(workspace_id=workspace_id, user_id=user_id)
    if payload.mode != "research_tool_assisted":
        raise ResearchAnalysisRunValidationError(
            "Background analysis runs currently support the research_tool_assisted mode only"
        )

    conversation = _ensure_conversation(
        workspace_id=workspace_id,
        user_id=user_id,
        question=payload.question,
        conversation_id=payload.conversation_id,
    )
    run = research_analysis_run_repository.create_research_analysis_run(
        workspace_id=workspace_id,
        conversation_id=conversation.id,
        created_by=user_id,
        question=payload.question.strip(),
        mode=payload.mode,
    )
    conversation_repository.create_message(
        conversation_id=conversation.id,
        role="user",
        content=payload.question.strip(),
        metadata_json={
            "mode": payload.mode,
            "research_analysis_run_id": run.id,
            "delivery": "background_run",
        },
    )
    conversation_repository.touch_conversation(conversation.id)

    try:
        await enqueue_research_analysis_run_execution(run.id)
    except ResearchAnalysisRunQueueError as error:
        failed_run = research_analysis_run_repository.update_research_analysis_run(
            run.id,
            next_status="failed",
            error_message=str(error),
        )
        if failed_run is None:
            raise ResearchAnalysisRunQueueError("Failed to enqueue the research analysis run") from error
        raise

    persisted = research_analysis_run_repository.get_research_analysis_run(run.id)
    if persisted is None:
        raise ResearchAnalysisRunAccessError("Research analysis run not found")
    return ResearchAnalysisRunResponse.from_model(persisted)


def get_research_analysis_run(*, run_id: str, user_id: str) -> ResearchAnalysisRunResponse | None:
    run = research_analysis_run_repository.get_research_analysis_run_for_user(run_id, user_id)
    if run is None:
        return None
    return ResearchAnalysisRunResponse.from_model(run)


def list_workspace_research_analysis_runs(*, workspace_id: str, user_id: str, limit: int = 12) -> list[ResearchAnalysisRunResponse]:
    _get_research_workspace_or_raise(workspace_id=workspace_id, user_id=user_id)
    normalized_limit = max(1, min(limit, 20))
    runs = research_analysis_run_repository.list_workspace_research_analysis_runs(
        workspace_id,
        user_id,
        limit=normalized_limit,
    )
    return [ResearchAnalysisRunResponse.from_model(run) for run in runs]


def _record_run_trace(
    *,
    run,
    answer: str,
    prompt: str,
    sources: list[dict[str, object]],
    tool_steps: list[dict[str, object]],
    analysis_focus: str | None,
    search_query: str | None,
    degraded_reason: str | None,
    token_input: int,
    token_output: int,
    started_at: datetime,
    error_message: str | None = None,
) -> str:
    latency_ms = max(int((datetime.now(UTC) - started_at).total_seconds() * 1000), 0)
    return record_chat_trace(
        workspace_id=run.workspace_id,
        conversation_id=run.conversation_id,
        question=run.question,
        answer=answer,
        mode=run.mode,
        sources=sources,
        retrieved_chunks=sources,
        prompt=prompt,
        latency_ms=latency_ms,
        token_input=token_input,
        token_output=token_output,
        estimated_cost=0.0,
        error=error_message,
        trace_type="research_tool_assisted_run",
        extra_response_json={
            "research_analysis_run_id": run.id,
            "run_status": "failed" if error_message else ("degraded" if degraded_reason else "completed"),
            "tool_steps": tool_steps,
            "analysis_focus": analysis_focus,
            "search_query": search_query,
            "degraded_reason": degraded_reason,
        },
        extra_metadata_json={
            "research_analysis_run_id": run.id,
            "analysis_focus": analysis_focus,
            "search_query": search_query,
            "degraded_reason": degraded_reason,
            "tool_steps": tool_steps,
        },
    )


def run_research_analysis_run_execution(run_id: str) -> dict[str, object]:
    run = research_analysis_run_repository.get_research_analysis_run(run_id)
    if run is None:
        raise ResearchAnalysisRunExecutionError("Research analysis run not found")

    if run.status != "pending":
        return {
            "run_id": run.id,
            "status": run.status,
            "skipped": True,
        }

    running_run = research_analysis_run_repository.update_research_analysis_run(
        run.id,
        next_status="running",
    )
    if running_run is None:
        raise ResearchAnalysisRunExecutionError("Research analysis run not found")

    started_at = datetime.now(UTC)
    try:
        result = run_tool_assisted_research_chat(
            workspace_id=running_run.workspace_id,
            user_id=running_run.created_by,
            question=running_run.question,
        )
        sources_json = [source.model_dump() for source in result.sources]
        tool_steps_json = [step.model_dump() for step in result.tool_steps]
        trace_id = _record_run_trace(
            run=running_run,
            answer=result.answer,
            prompt=result.prompt,
            sources=sources_json,
            tool_steps=tool_steps_json,
            analysis_focus=result.analysis_focus,
            search_query=result.search_query,
            degraded_reason=result.degraded_reason,
            token_input=result.token_input,
            token_output=result.token_output,
            started_at=started_at,
        )
        conversation_repository.create_message(
            conversation_id=running_run.conversation_id,
            role="assistant",
            content=result.answer,
            metadata_json={
                "mode": running_run.mode,
                "sources": sources_json,
                "research_analysis_run_id": running_run.id,
                "delivery": "background_run",
            },
        )
        conversation_repository.touch_conversation(running_run.conversation_id)

        terminal_status = "degraded" if result.degraded_reason else "completed"
        completed_run = research_analysis_run_repository.update_research_analysis_run(
            running_run.id,
            next_status=terminal_status,
            prompt=result.prompt,
            answer=result.answer,
            trace_id=trace_id,
            sources_json=sources_json,
            tool_steps_json=tool_steps_json,
            analysis_focus=result.analysis_focus,
            search_query=result.search_query,
            degraded_reason=result.degraded_reason,
        )
        if completed_run is None:
            raise ResearchAnalysisRunExecutionError("Research analysis run not found")
        return {
            "run_id": completed_run.id,
            "status": completed_run.status,
            "trace_id": completed_run.trace_id,
        }
    except ChatProcessingError as error:
        trace_id = _record_run_trace(
            run=running_run,
            answer="",
            prompt="",
            sources=[],
            tool_steps=[],
            analysis_focus=None,
            search_query=None,
            degraded_reason=None,
            token_input=0,
            token_output=0,
            started_at=started_at,
            error_message=str(error),
        )
        failed_run = research_analysis_run_repository.update_research_analysis_run(
            running_run.id,
            next_status="failed",
            trace_id=trace_id,
            error_message=str(error),
        )
        if failed_run is None:
            raise ResearchAnalysisRunExecutionError("Research analysis run not found") from error
        raise ResearchAnalysisRunExecutionError(str(error)) from error
    except Exception as error:
        trace_id = _record_run_trace(
            run=running_run,
            answer="",
            prompt="",
            sources=[],
            tool_steps=[],
            analysis_focus=None,
            search_query=None,
            degraded_reason=None,
            token_input=0,
            token_output=0,
            started_at=started_at,
            error_message=str(error),
        )
        failed_run = research_analysis_run_repository.update_research_analysis_run(
            running_run.id,
            next_status="failed",
            trace_id=trace_id,
            error_message=str(error),
        )
        if failed_run is None:
            raise ResearchAnalysisRunExecutionError("Research analysis run not found") from error
        raise ResearchAnalysisRunExecutionError("Research analysis run failed") from error
