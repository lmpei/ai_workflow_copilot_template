from app.repositories import research_analysis_run_repository, trace_repository, workspace_repository
from app.schemas.research_analysis_review import ResearchAnalysisReviewRecord, ResearchAnalysisReviewResponse
from app.services.chat_evaluator_service import (
    RESEARCH_ANALYSIS_RUN_REGRESSION_BASELINE_VERSION,
    evaluate_research_analysis_run_regression,
)
from app.services.research_analysis_run_service import ResearchAnalysisRunAccessError, ResearchAnalysisRunValidationError


_TERMINAL_REVIEW_STATUSES = {"completed", "degraded", "failed"}


def _get_research_workspace_or_raise(*, workspace_id: str, user_id: str):
    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        raise ResearchAnalysisRunAccessError("Workspace not found")
    if workspace.module_type != "research":
        raise ResearchAnalysisRunValidationError("Research analysis review is only available in Research workspaces")
    return workspace


def list_workspace_research_analysis_review(
    *,
    workspace_id: str,
    user_id: str,
    limit: int = 10,
) -> ResearchAnalysisReviewResponse:
    _get_research_workspace_or_raise(workspace_id=workspace_id, user_id=user_id)
    normalized_limit = max(1, min(limit, 20))
    runs = research_analysis_run_repository.list_workspace_research_analysis_runs(
        workspace_id,
        user_id,
        limit=normalized_limit * 3,
    )
    terminal_runs = [run for run in runs if run.status in _TERMINAL_REVIEW_STATUSES][:normalized_limit]

    traces = trace_repository.list_traces_for_workspace(workspace_id)
    trace_by_id = {trace.id: trace for trace in traces}

    items: list[ResearchAnalysisReviewRecord] = []
    for run in terminal_runs:
        trace = trace_by_id.get(run.trace_id) if run.trace_id else None
        baseline = evaluate_research_analysis_run_regression(
            run_json={
                "status": run.status,
                "mode": run.mode,
                "trace_id": run.trace_id,
                "answer": run.answer,
                "sources": run.sources_json,
                "tool_steps": run.tool_steps_json,
                "run_memory": run.run_memory_json,
                "degraded_reason": run.degraded_reason,
                "resumed_from_run_id": run.resumed_from_run_id,
                "selected_external_resource_snapshot_id": run.selected_external_resource_snapshot_id,
                "external_resource_snapshot_id": run.external_resource_snapshot_id,
            },
            trace_response_json=trace.response_json if trace is not None else None,
            trace_metadata=trace.metadata_json if trace is not None else None,
            trace_type=trace.trace_type if trace is not None else None,
        )
        signals = baseline.get("signals") if isinstance(baseline.get("signals"), dict) else {}
        run_memory_summary = None
        if isinstance(run.run_memory_json, dict):
            summary = run.run_memory_json.get("summary")
            if isinstance(summary, str) and summary.strip():
                run_memory_summary = summary.strip()
        selected_snapshot_id = (
            signals.get("selected_external_resource_snapshot_id")
            if isinstance(signals.get("selected_external_resource_snapshot_id"), str)
            else None
        )
        external_snapshot_id = (
            signals.get("external_resource_snapshot_id")
            if isinstance(signals.get("external_resource_snapshot_id"), str)
            else None
        )
        selected_snapshot_title = None
        external_snapshot_title = None
        mcp_server_id = signals.get("mcp_server_id") if isinstance(signals.get("mcp_server_id"), str) else None
        mcp_resource_id = signals.get("mcp_resource_id") if isinstance(signals.get("mcp_resource_id"), str) else None
        mcp_resource_uri = signals.get("mcp_resource_uri") if isinstance(signals.get("mcp_resource_uri"), str) else None
        mcp_resource_display_name = (
            signals.get("mcp_resource_display_name")
            if isinstance(signals.get("mcp_resource_display_name"), str)
            else None
        )
        if selected_snapshot_id:
            selected_snapshot = research_analysis_run_repository.get_research_external_resource_snapshot(selected_snapshot_id)
            if selected_snapshot is not None:
                selected_snapshot_title = selected_snapshot.title
        if external_snapshot_id:
            external_snapshot = research_analysis_run_repository.get_research_external_resource_snapshot(external_snapshot_id)
            if external_snapshot is not None:
                external_snapshot_title = external_snapshot.title

        items.append(
            ResearchAnalysisReviewRecord(
                run_id=run.id,
                question=run.question,
                status=run.status,
                mode=run.mode,
                trace_id=run.trace_id,
                resumed_from_run_id=run.resumed_from_run_id,
                degraded_reason=run.degraded_reason,
                run_memory_summary=run_memory_summary,
                connector_id=signals.get("connector_id") if isinstance(signals.get("connector_id"), str) else None,
                connector_consent_state=(
                    signals.get("connector_consent_state")
                    if isinstance(signals.get("connector_consent_state"), str)
                    else None
                ),
                external_context_used=(
                    signals.get("external_context_used")
                    if isinstance(signals.get("external_context_used"), bool)
                    else None
                ),
                external_match_count=(
                    signals.get("external_match_count")
                    if isinstance(signals.get("external_match_count"), int)
                    else None
                ),
                selected_external_resource_snapshot_id=selected_snapshot_id,
                selected_external_resource_snapshot_title=selected_snapshot_title,
                external_resource_snapshot_id=external_snapshot_id,
                external_resource_snapshot_title=external_snapshot_title,
                resource_selection_mode=(
                    signals.get("resource_selection_mode")
                    if isinstance(signals.get("resource_selection_mode"), str)
                    else None
                ),
                context_selection_mode=(
                    signals.get("context_selection_mode")
                    if isinstance(signals.get("context_selection_mode"), str)
                    else None
                ),
                mcp_server_id=mcp_server_id,
                mcp_resource_id=mcp_resource_id,
                mcp_resource_uri=mcp_resource_uri,
                mcp_resource_display_name=mcp_resource_display_name,
                passed=bool(baseline["passed"]),
                issues=[str(item) for item in baseline["issues"]],
                regression_baseline=baseline,
                created_at=run.created_at,
                completed_at=run.completed_at,
            )
        )

    passing_count = sum(1 for item in items if item.passed)
    return ResearchAnalysisReviewResponse(
        baseline_version=RESEARCH_ANALYSIS_RUN_REGRESSION_BASELINE_VERSION,
        reviewed_count=len(items),
        passing_count=passing_count,
        failing_count=len(items) - passing_count,
        items=items,
    )
