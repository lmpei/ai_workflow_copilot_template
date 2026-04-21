from datetime import UTC, datetime

from app.repositories import (
    ai_hot_tracker_tracking_run_repository,
    workspace_repository,
)
from app.schemas.ai_frontier_research import (
    AiFrontierResearchOutput,
    AiFrontierTheme,
    AiHotTrackerReportResponse,
    AiHotTrackerTrackingProfile,
    AiHotTrackerTrackingRunCreateRequest,
    AiHotTrackerTrackingRunDelta,
    AiHotTrackerTrackingRunFollowUpRequest,
    AiHotTrackerTrackingRunFollowUpResponse,
    AiHotTrackerTrackingRunResponse,
    normalize_ai_hot_tracker_tracking_profile,
)
from app.services.ai_hot_tracker_follow_up_service import (
    answer_ai_hot_tracker_tracking_run_follow_up,
)
from app.services.ai_hot_tracker_report_service import (
    filter_ai_hot_tracker_source_intake,
    generate_ai_hot_tracker_report_from_intake,
)
from app.services.ai_hot_tracker_source_service import fetch_ai_hot_tracker_source_items
from app.services.retrieval_generation_service import ChatProcessingError


class AiHotTrackerTrackingAccessError(Exception):
    pass


def _resolve_tracking_profile(module_config_json: dict[str, object] | None) -> AiHotTrackerTrackingProfile:
    config = module_config_json if isinstance(module_config_json, dict) else {}
    tracking_profile = config.get("tracking_profile")
    return normalize_ai_hot_tracker_tracking_profile(
        tracking_profile if isinstance(tracking_profile, dict) else None
    )


def _build_delta(
    *,
    previous_run: AiHotTrackerTrackingRunResponse | None,
    report: AiHotTrackerReportResponse,
    tracking_profile: AiHotTrackerTrackingProfile,
    status: str,
) -> AiHotTrackerTrackingRunDelta:
    if status == "failed":
        return AiHotTrackerTrackingRunDelta(
            previous_run_id=previous_run.id if previous_run else None,
            change_state="degraded",
            summary="本轮运行失败，未能形成可比较的追踪结果。",
            should_notify=False,
        )

    if previous_run is None:
        return AiHotTrackerTrackingRunDelta(
            previous_run_id=None,
            change_state="first_run",
            summary="这是这个工作区的第一轮追踪，后续结果将从下一轮开始比较变化。",
            should_notify=True,
            new_item_count=len(report.source_items),
            new_titles=[item.title for item in report.source_items[:4]],
        )

    current_by_url = {item.url: item for item in report.source_items}
    previous_by_url = {item.url: item for item in previous_run.source_items}

    current_urls = set(current_by_url)
    previous_urls = set(previous_by_url)

    new_urls = current_urls - previous_urls
    continuing_urls = current_urls & previous_urls
    cooled_down_urls = previous_urls - current_urls

    new_titles = [current_by_url[url].title for url in list(new_urls)[:4]]
    continuing_titles = [current_by_url[url].title for url in list(continuing_urls)[:4]]
    cooled_down_titles = [previous_by_url[url].title for url in list(cooled_down_urls)[:4]]

    if report.degraded_reason:
        return AiHotTrackerTrackingRunDelta(
            previous_run_id=previous_run.id,
            change_state="degraded",
            summary="本轮来源已经更新，但结构化判断不完整，应将结果视为降级输出。",
            should_notify=False,
            new_item_count=len(new_urls),
            continuing_item_count=len(continuing_urls),
            cooled_down_item_count=len(cooled_down_urls),
            new_titles=new_titles,
            continuing_titles=continuing_titles,
            cooled_down_titles=cooled_down_titles,
        )

    has_meaningful_change = len(new_urls) >= tracking_profile.alert_threshold
    if has_meaningful_change:
        summary = (
            f"相较上一轮，新增 {len(new_urls)} 条值得关注的线索，"
            f"延续 {len(continuing_urls)} 条，降温 {len(cooled_down_urls)} 条。"
        )
        change_state = "meaningful_update"
    else:
        summary = (
            f"相较上一轮，新增变化不足 {tracking_profile.alert_threshold} 条，"
            "当前更接近延续跟踪而不是明显转折。"
        )
        change_state = "steady_state"

    return AiHotTrackerTrackingRunDelta(
        previous_run_id=previous_run.id,
        change_state=change_state,
        summary=summary,
        should_notify=has_meaningful_change,
        new_item_count=len(new_urls),
        continuing_item_count=len(continuing_urls),
        cooled_down_item_count=len(cooled_down_urls),
        new_titles=new_titles,
        continuing_titles=continuing_titles,
        cooled_down_titles=cooled_down_titles,
    )


def _persist_run(
    *,
    workspace_id: str,
    previous_run_id: str | None,
    user_id: str,
    trigger_kind: str,
    status: str,
    report: AiHotTrackerReportResponse,
    tracking_profile: AiHotTrackerTrackingProfile,
    delta: AiHotTrackerTrackingRunDelta,
    error_message: str | None = None,
) -> AiHotTrackerTrackingRunResponse:
    run = ai_hot_tracker_tracking_run_repository.create_ai_hot_tracker_tracking_run(
        workspace_id=workspace_id,
        previous_run_id=previous_run_id,
        created_by=user_id,
        trigger_kind=trigger_kind,
        status=status,
        title=report.title,
        question=report.question,
        profile_snapshot_json=tracking_profile.model_dump(mode="json"),
        output_json=report.output.model_dump(mode="json"),
        source_catalog_json=[item.model_dump(mode="json") for item in report.source_catalog],
        source_items_json=[item.model_dump(mode="json") for item in report.source_items],
        source_failures_json=[item.model_dump(mode="json") for item in report.source_failures],
        source_set_json=report.source_set,
        delta_json=delta.model_dump(mode="json"),
        follow_ups_json=[],
        degraded_reason=report.degraded_reason,
        error_message=error_message,
        generated_at=report.generated_at,
    )
    return AiHotTrackerTrackingRunResponse.from_model(run)


def _build_failed_report(
    *,
    tracking_profile: AiHotTrackerTrackingProfile,
    generated_at: datetime,
    error_message: str,
) -> AiHotTrackerReportResponse:
    return AiHotTrackerReportResponse(
        title="本轮运行失败",
        question=f"请围绕「{tracking_profile.topic}」继续追踪。",
        output=AiFrontierResearchOutput(
            frontier_summary="这次运行没有成功完成，因此没有产生可用简报。",
            trend_judgment="请先检查来源抓取、模型输出或服务状态，然后重新运行。",
            themes=[AiFrontierTheme(label="运行失败", summary=error_message)],
            events=[],
            project_cards=[],
            reference_sources=[],
        ),
        source_catalog=[],
        source_items=[],
        source_failures=[],
        source_set={
            "mode": "ai_hot_tracker_tracking_agent",
            "generated_at": generated_at.isoformat(),
            "tracking_profile": tracking_profile.model_dump(mode="json"),
            "error_message": error_message,
        },
        generated_at=generated_at,
        degraded_reason="tracking_run_failed",
    )


def create_ai_hot_tracker_tracking_run(
    *,
    workspace_id: str,
    user_id: str,
    payload: AiHotTrackerTrackingRunCreateRequest | None = None,
) -> AiHotTrackerTrackingRunResponse:
    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        raise AiHotTrackerTrackingAccessError("Workspace not found")
    if workspace.module_type != "research":
        raise AiHotTrackerTrackingAccessError("AI hot tracker is only available in research workspaces")

    request = payload or AiHotTrackerTrackingRunCreateRequest()
    tracking_profile = _resolve_tracking_profile(workspace.module_config_json)
    previous_run_model = ai_hot_tracker_tracking_run_repository.get_latest_workspace_ai_hot_tracker_tracking_run(
        workspace_id=workspace_id
    )
    previous_run = (
        AiHotTrackerTrackingRunResponse.from_model(previous_run_model)
        if previous_run_model is not None
        else None
    )

    try:
        intake = filter_ai_hot_tracker_source_intake(
            intake=fetch_ai_hot_tracker_source_items(total_limit=tracking_profile.max_items_per_run),
            tracking_profile=tracking_profile,
        )
        report = generate_ai_hot_tracker_report_from_intake(
            intake=intake,
            tracking_profile=tracking_profile,
        )
        status = "degraded" if report.degraded_reason else "completed"
        delta = _build_delta(
            previous_run=previous_run,
            report=report,
            tracking_profile=tracking_profile,
            status=status,
        )
        return _persist_run(
            workspace_id=workspace_id,
            previous_run_id=previous_run.id if previous_run else None,
            user_id=user_id,
            trigger_kind=request.trigger_kind,
            status=status,
            report=report,
            tracking_profile=tracking_profile,
            delta=delta,
        )
    except Exception as error:
        generated_at = datetime.now(UTC)
        report = _build_failed_report(
            tracking_profile=tracking_profile,
            generated_at=generated_at,
            error_message=str(error),
        )
        delta = _build_delta(
            previous_run=previous_run,
            report=report,
            tracking_profile=tracking_profile,
            status="failed",
        )
        return _persist_run(
            workspace_id=workspace_id,
            previous_run_id=previous_run.id if previous_run else None,
            user_id=user_id,
            trigger_kind=request.trigger_kind,
            status="failed",
            report=report,
            tracking_profile=tracking_profile,
            delta=delta,
            error_message=str(error),
        )


def list_workspace_ai_hot_tracker_tracking_runs(
    *,
    workspace_id: str,
    user_id: str,
    limit: int = 12,
) -> list[AiHotTrackerTrackingRunResponse]:
    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        raise AiHotTrackerTrackingAccessError("Workspace not found")

    runs = ai_hot_tracker_tracking_run_repository.list_workspace_ai_hot_tracker_tracking_runs(
        workspace_id=workspace_id,
        user_id=user_id,
        limit=max(1, min(limit, 20)),
    )
    return [AiHotTrackerTrackingRunResponse.from_model(run) for run in runs]


def get_ai_hot_tracker_tracking_run(
    *,
    run_id: str,
    user_id: str,
) -> AiHotTrackerTrackingRunResponse | None:
    run = ai_hot_tracker_tracking_run_repository.get_ai_hot_tracker_tracking_run_for_user(
        run_id=run_id,
        user_id=user_id,
    )
    if run is None:
        return None
    return AiHotTrackerTrackingRunResponse.from_model(run)


def delete_ai_hot_tracker_tracking_run(*, run_id: str, user_id: str) -> bool:
    return ai_hot_tracker_tracking_run_repository.delete_ai_hot_tracker_tracking_run(
        run_id=run_id,
        user_id=user_id,
    )


def answer_ai_hot_tracker_follow_up(
    *,
    run_id: str,
    user_id: str,
    payload: AiHotTrackerTrackingRunFollowUpRequest,
) -> AiHotTrackerTrackingRunFollowUpResponse:
    run = get_ai_hot_tracker_tracking_run(run_id=run_id, user_id=user_id)
    if run is None:
        raise AiHotTrackerTrackingAccessError("AI hot tracker run not found")

    try:
        response = answer_ai_hot_tracker_tracking_run_follow_up(
            run=run,
            payload=payload,
        )
    except ChatProcessingError:
        raise

    updated_follow_ups = [
        *[item.model_dump(mode="json") for item in run.follow_ups],
        response.follow_up.model_dump(mode="json"),
    ]
    ai_hot_tracker_tracking_run_repository.update_ai_hot_tracker_tracking_run_follow_ups(
        run_id=run_id,
        user_id=user_id,
        follow_ups_json=updated_follow_ups,
    )
    return response
