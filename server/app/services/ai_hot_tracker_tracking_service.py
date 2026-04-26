from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.models.workspace import Workspace
from app.repositories import (
    ai_hot_tracker_signal_memory_repository,
    ai_hot_tracker_tracking_run_repository,
    ai_hot_tracker_tracking_state_repository,
    workspace_repository,
)
from app.schemas.ai_frontier_research import (
    AiHotTrackerAgentRoleTrace,
    AiHotTrackerBriefOutput,
    AiHotTrackerClusterSnapshot,
    AiHotTrackerJudgmentFinding,
    AiHotTrackerReportResponse,
    AiHotTrackerRunEvaluationResponse,
    AiHotTrackerSignalCluster,
    AiHotTrackerSignalMemoryRecord,
    AiHotTrackerTrackingProfile,
    AiHotTrackerTrackingRunCreateRequest,
    AiHotTrackerTrackingRunDelta,
    AiHotTrackerTrackingRunFollowUpRequest,
    AiHotTrackerTrackingRunFollowUpResponse,
    AiHotTrackerTrackingRunResponse,
    AiHotTrackerTrackingStateResponse,
    normalize_ai_hot_tracker_tracking_profile,
)
from app.services.ai_hot_tracker_decision_service import (
    AiHotTrackerDecisionResult,
    build_signal_decision_result,
    build_tracking_delta,
    deserialize_cluster_snapshot,
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

_CADENCE_INTERVALS: dict[str, timedelta] = {
    "daily": timedelta(days=1),
    "twice_daily": timedelta(hours=12),
    "weekly": timedelta(days=7),
}


class AiHotTrackerTrackingAccessError(Exception):
    pass


@dataclass(slots=True)
class _TrackingExecutionResult:
    run: AiHotTrackerTrackingRunResponse | None
    status: str
    delta: AiHotTrackerTrackingRunDelta


def _resolve_tracking_profile(module_config_json: dict[str, object] | None) -> AiHotTrackerTrackingProfile:
    config = module_config_json if isinstance(module_config_json, dict) else {}
    tracking_profile = config.get("tracking_profile")
    return normalize_ai_hot_tracker_tracking_profile(
        tracking_profile if isinstance(tracking_profile, dict) else None
    )


def _resolve_next_due_at(reference_time: datetime, cadence: str) -> datetime | None:
    interval = _CADENCE_INTERVALS.get(cadence)
    if interval is None:
        return None
    return reference_time + interval


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _should_persist_scheduled_run(
    *,
    status: str,
    delta: AiHotTrackerTrackingRunDelta,
) -> bool:
    if status in {"failed", "degraded"}:
        return True
    return delta.change_state in {"first_run", "meaningful_update"}


def _build_failed_report(
    *,
    tracking_profile: AiHotTrackerTrackingProfile,
    generated_at: datetime,
    error_message: str,
) -> AiHotTrackerReportResponse:
    output = AiHotTrackerBriefOutput(
        headline="本轮追踪失败",
        summary="这次运行没有成功完成，因此暂时没有可用的热点简报。",
        change_state="failed",
        signals=[],
        keep_watching=[],
        blindspots=["系统未能完成这一轮判断，建议根据错误原因稍后重试。"],
        reference_sources=[],
    )
    return AiHotTrackerReportResponse(
        title=output.headline,
        question=f"请围绕“{tracking_profile.topic}”继续追踪。",
        output=output,
        source_catalog=[],
        source_items=[],
        source_failures=[],
        source_set={
            "mode": "ai_hot_tracker_tracking_agent",
            "generated_at": generated_at.isoformat(),
            "tracking_profile": tracking_profile.model_dump(mode="json"),
            "error_message": error_message,
            "agent_trace": [
                {
                    "role": "evaluator",
                    "summary": "本轮运行在生成可用简报前失败，已记录真实错误原因。",
                    "status": "failed",
                    "details": {"error_message": error_message},
                }
            ],
        },
        generated_at=generated_at,
        degraded_reason="tracking_run_failed",
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


def _load_previous_run(workspace_id: str) -> AiHotTrackerTrackingRunResponse | None:
    previous_run_model = ai_hot_tracker_tracking_run_repository.get_latest_workspace_ai_hot_tracker_tracking_run(
        workspace_id=workspace_id
    )
    if previous_run_model is None:
        return None
    return AiHotTrackerTrackingRunResponse.from_model(previous_run_model)


def _rebuild_cluster_snapshot_from_run(
    run: AiHotTrackerTrackingRunResponse,
) -> list[AiHotTrackerClusterSnapshot]:
    source_set = run.source_set if isinstance(run.source_set, dict) else {}
    cluster_snapshot = deserialize_cluster_snapshot(source_set.get("cluster_snapshot"))
    if cluster_snapshot:
        return cluster_snapshot

    decision_result = build_signal_decision_result(
        source_catalog=run.source_catalog,
        source_items=run.source_items,
        tracking_profile=run.profile,
        previous_snapshot=None,
        reference_time=run.generated_at,
    )
    return decision_result.cluster_snapshot


def _load_signal_memories(
    *,
    workspace_id: str,
) -> list[AiHotTrackerSignalMemoryRecord]:
    memories = ai_hot_tracker_signal_memory_repository.list_workspace_ai_hot_tracker_signal_memories(
        workspace_id=workspace_id
    )
    return [
        AiHotTrackerSignalMemoryRecord(
            event_id=memory.id,
            fingerprint=memory.fingerprint,
            title=memory.title,
            category=memory.category,
            first_seen_at=_normalize_datetime(memory.first_seen_at) or datetime.now(UTC),
            last_seen_at=_normalize_datetime(memory.last_seen_at) or datetime.now(UTC),
            continuity_state=memory.continuity_state,
            activity_state=memory.activity_state,
            source_families=[
                item
                for item in memory.source_families_json
                if isinstance(item, str)
            ],
            source_item_ids=[
                item
                for item in memory.source_item_ids_json
                if isinstance(item, str)
            ],
            source_labels=[
                item
                for item in memory.source_labels_json
                if isinstance(item, str)
            ],
            latest_priority_level=memory.latest_priority_level,
            latest_rank_score=memory.latest_rank_score,
            last_seen_run_id=memory.last_seen_run_id,
            streak_count=memory.streak_count,
            cooling_since=_normalize_datetime(memory.cooling_since),
            superseded_by_event_id=memory.superseded_by_event_id,
            last_cluster_snapshot=(
                memory.last_cluster_snapshot_json
                if isinstance(memory.last_cluster_snapshot_json, dict)
                else {}
            ),
            note=memory.note,
        )
        for memory in memories
    ]


def _store_signal_memories(
    *,
    workspace_id: str,
    decision_result: AiHotTrackerDecisionResult,
    run_id: str | None,
) -> None:
    ai_hot_tracker_signal_memory_repository.upsert_workspace_ai_hot_tracker_signal_memories(
        workspace_id=workspace_id,
        records=[
            {
                **memory.model_dump(mode="python"),
                "last_seen_run_id": run_id,
            }
            for memory in decision_result.signal_memories
        ],
    )


def _load_previous_snapshot(
    *,
    workspace_id: str,
) -> tuple[list[AiHotTrackerClusterSnapshot], str | None]:
    tracking_state = ai_hot_tracker_tracking_state_repository.get_ai_hot_tracker_tracking_state(
        workspace_id=workspace_id
    )
    if tracking_state is not None:
        snapshot = deserialize_cluster_snapshot(tracking_state.last_cluster_snapshot_json)
        previous_run_id = tracking_state.last_saved_run_id
        if previous_run_id is not None:
            previous_run = ai_hot_tracker_tracking_run_repository.get_ai_hot_tracker_tracking_run(
                run_id=previous_run_id
            )
            if previous_run is None:
                previous_run_id = None
        if snapshot:
            return snapshot, previous_run_id
        if previous_run_id is not None:
            previous_run = ai_hot_tracker_tracking_run_repository.get_ai_hot_tracker_tracking_run(
                run_id=previous_run_id
            )
            if previous_run is not None:
                rebuilt_run = AiHotTrackerTrackingRunResponse.from_model(previous_run)
                return _rebuild_cluster_snapshot_from_run(rebuilt_run), previous_run_id
        return [], previous_run_id

    previous_run = _load_previous_run(workspace_id)
    if previous_run is None:
        return [], None
    return _rebuild_cluster_snapshot_from_run(previous_run), previous_run.id


def _store_tracking_state(
    *,
    workspace_id: str,
    reference_time: datetime,
    tracking_profile: AiHotTrackerTrackingProfile,
    decision_result: AiHotTrackerDecisionResult | None,
    saved_run_id: str | None,
    saved_run_generated_at: datetime | None,
    notified_run_id: str | None,
    latest_meaningful_update_at: datetime | None,
    status: str,
    error_message: str | None,
) -> None:
    existing_state = ai_hot_tracker_tracking_state_repository.get_ai_hot_tracker_tracking_state(
        workspace_id=workspace_id
    )
    consecutive_failure_count = 0
    last_successful_scan_at = (
        reference_time
        if status != "failed"
        else (existing_state.last_successful_scan_at if existing_state is not None else None)
    )
    if decision_result is None:
        last_cluster_snapshot_json = (
            existing_state.last_cluster_snapshot_json if existing_state is not None else []
        )
    else:
        last_cluster_snapshot_json = [
            snapshot.model_dump(mode="json") for snapshot in decision_result.cluster_snapshot
        ]

    if status == "failed":
        consecutive_failure_count = (
            (existing_state.consecutive_failure_count if existing_state is not None else 0) + 1
        )

    ai_hot_tracker_tracking_state_repository.upsert_ai_hot_tracker_tracking_state(
        workspace_id=workspace_id,
        last_checked_at=reference_time,
        last_evaluated_at=reference_time,
        last_successful_scan_at=last_successful_scan_at,
        next_due_at=_resolve_next_due_at(reference_time, tracking_profile.cadence),
        last_cluster_snapshot_json=last_cluster_snapshot_json,
        last_saved_run_id=saved_run_id
        or (existing_state.last_saved_run_id if existing_state is not None else None),
        latest_saved_run_generated_at=saved_run_generated_at
        or (existing_state.latest_saved_run_generated_at if existing_state is not None else None),
        last_notified_run_id=notified_run_id
        or (existing_state.last_notified_run_id if existing_state is not None else None),
        latest_meaningful_update_at=latest_meaningful_update_at
        or (existing_state.latest_meaningful_update_at if existing_state is not None else None),
        consecutive_failure_count=consecutive_failure_count,
        last_error_message=error_message,
    )


def _priority_rank(value: str) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(value, 1)


def _resolve_expected_signal_change_type(cluster: AiHotTrackerSignalCluster) -> str:
    if cluster.is_new:
        return "new"
    if cluster.is_cooling:
        return "cooling"
    return "continuing"


_BRIEF_ALIGNMENT_CHECK_CODES = {
    "brief_change_state_matches_delta",
    "brief_signals_have_grounding_sources",
    "high_priority_clusters_surface_in_brief",
    "brief_signal_cluster_consistency",
    "brief_signal_priority_alignment",
    "brief_signal_change_type_alignment",
}

_FOLLOW_UP_GROUNDING_CHECK_CODES = {
    "follow_up_grounding_visibility",
}


def _partition_run_quality_checks(
    findings: list[AiHotTrackerJudgmentFinding],
) -> tuple[
    list[AiHotTrackerJudgmentFinding],
    list[AiHotTrackerJudgmentFinding],
    list[AiHotTrackerJudgmentFinding],
]:
    judgment_findings: list[AiHotTrackerJudgmentFinding] = []
    brief_alignment_checks: list[AiHotTrackerJudgmentFinding] = []
    follow_up_grounding_checks: list[AiHotTrackerJudgmentFinding] = []

    for finding in findings:
        if finding.code in _BRIEF_ALIGNMENT_CHECK_CODES:
            brief_alignment_checks.append(finding)
            continue
        if finding.code in _FOLLOW_UP_GROUNDING_CHECK_CODES:
            follow_up_grounding_checks.append(finding)
            continue
        judgment_findings.append(finding)

    return judgment_findings, brief_alignment_checks, follow_up_grounding_checks


def _build_run_quality_checks(
    *,
    run: AiHotTrackerTrackingRunResponse,
    clustered_signals: list[AiHotTrackerSignalCluster],
    event_memories: list[AiHotTrackerSignalMemoryRecord],
) -> list[AiHotTrackerJudgmentFinding]:
    findings: list[AiHotTrackerJudgmentFinding] = []
    source_item_ids = {item.id for item in run.source_items}
    cluster_by_item_id = {
        item_id: cluster
        for cluster in clustered_signals
        for item_id in cluster.source_item_ids
    }
    source_set = run.source_set if isinstance(run.source_set, dict) else {}
    raw_candidate_cluster_ids = source_set.get("candidate_cluster_ids", [])
    candidate_cluster_ids = {
        cluster_id
        for cluster_id in raw_candidate_cluster_ids
        if isinstance(cluster_id, str)
    }
    evaluation_clusters = (
        [cluster for cluster in clustered_signals if cluster.cluster_id in candidate_cluster_ids]
        if candidate_cluster_ids
        else clustered_signals
    )

    expected_new_count = sum(1 for cluster in clustered_signals if cluster.is_new)
    expected_continuing_count = sum(1 for cluster in clustered_signals if cluster.is_continuing)
    expected_cooled_count = sum(1 for memory in event_memories if memory.continuity_state == "cooling")
    delta_matches = (
        run.delta.new_item_count == expected_new_count
        and run.delta.continuing_item_count == expected_continuing_count
        and run.delta.cooled_down_item_count == expected_cooled_count
    )
    findings.append(
        AiHotTrackerJudgmentFinding(
            code="delta_cluster_consistency",
            status="pass" if delta_matches else "fail",
            summary=(
                "delta 统计与当前簇状态一致。"
                if delta_matches
                else "delta 统计与当前簇状态不一致，需要检查 new / continuing / cooling 计数。"
            ),
            details={
                "reported": {
                    "new": run.delta.new_item_count,
                    "continuing": run.delta.continuing_item_count,
                    "cooling": run.delta.cooled_down_item_count,
                },
                "computed": {
                    "new": expected_new_count,
                    "continuing": expected_continuing_count,
                    "cooling": expected_cooled_count,
                },
            },
        )
    )

    findings.append(
        AiHotTrackerJudgmentFinding(
            code="brief_change_state_matches_delta",
            status="pass" if run.output.change_state == run.delta.change_state else "fail",
            summary=(
                "简报变化状态与 delta 判断一致。"
                if run.output.change_state == run.delta.change_state
                else "简报变化状态与 delta 判断不一致，产品层表达不够诚实。"
            ),
            details={
                "brief_change_state": run.output.change_state,
                "delta_change_state": run.delta.change_state,
            },
        )
    )

    invalid_signal_titles = [
        signal.title
        for signal in run.output.signals
        if not signal.source_item_ids or any(item_id not in source_item_ids for item_id in signal.source_item_ids)
    ]
    findings.append(
        AiHotTrackerJudgmentFinding(
            code="brief_signals_have_grounding_sources",
            status="pass" if not invalid_signal_titles else "fail",
            summary=(
                "简报主信号都能回溯到当前来源条目。"
                if not invalid_signal_titles
                else "有主信号缺少来源锚点，简报与内部判断没有完全对齐。"
            ),
            details={"invalid_signal_titles": invalid_signal_titles},
        )
    )

    surfaced_high_priority_cluster_ids: set[str] = set()
    multi_cluster_signal_titles: list[str] = []
    unclustered_signal_titles: list[str] = []
    overstated_priority_signals: list[dict[str, object]] = []
    understated_priority_signals: list[dict[str, object]] = []
    change_type_mismatches: list[dict[str, object]] = []

    for signal in run.output.signals:
        referenced_clusters: list[AiHotTrackerSignalCluster] = []
        seen_cluster_ids: set[str] = set()
        for item_id in signal.source_item_ids:
            cluster = cluster_by_item_id.get(item_id)
            if cluster is None or cluster.cluster_id in seen_cluster_ids:
                continue
            seen_cluster_ids.add(cluster.cluster_id)
            referenced_clusters.append(cluster)

        if not referenced_clusters:
            unclustered_signal_titles.append(signal.title)
            continue

        for cluster in referenced_clusters:
            if cluster.priority_level == "high":
                surfaced_high_priority_cluster_ids.add(cluster.cluster_id)

        if len(referenced_clusters) > 1:
            multi_cluster_signal_titles.append(signal.title)

        expected_priority = max(
            referenced_clusters,
            key=lambda cluster: _priority_rank(cluster.priority_level),
        ).priority_level
        signal_priority_rank = _priority_rank(signal.priority_level)
        expected_priority_rank = _priority_rank(expected_priority)
        if signal_priority_rank > expected_priority_rank:
            overstated_priority_signals.append(
                {
                    "title": signal.title,
                    "signal_priority": signal.priority_level,
                    "expected_priority": expected_priority,
                }
            )
        elif signal_priority_rank < expected_priority_rank:
            understated_priority_signals.append(
                {
                    "title": signal.title,
                    "signal_priority": signal.priority_level,
                    "expected_priority": expected_priority,
                }
            )

        expected_change_types = {
            _resolve_expected_signal_change_type(cluster)
            for cluster in referenced_clusters
        }
        if len(expected_change_types) == 1:
            expected_change_type = next(iter(expected_change_types))
            if signal.change_type != expected_change_type:
                change_type_mismatches.append(
                    {
                        "title": signal.title,
                        "signal_change_type": signal.change_type,
                        "expected_change_type": expected_change_type,
                    }
                )

    high_priority_clusters = [
        cluster for cluster in evaluation_clusters if cluster.priority_level == "high"
    ]
    missing_high_priority_clusters = [
        cluster.title
        for cluster in high_priority_clusters
        if cluster.cluster_id not in surfaced_high_priority_cluster_ids
    ]
    findings.append(
        AiHotTrackerJudgmentFinding(
            code="high_priority_clusters_surface_in_brief",
            status="pass" if not missing_high_priority_clusters else "fail",
            summary=(
                "高优先级候选信号都出现在主简报里。"
                if not missing_high_priority_clusters
                else "有高优先级候选没有出现在主简报里。"
            ),
            details={
                "high_priority_cluster_titles": [cluster.title for cluster in high_priority_clusters],
                "missing_high_priority_cluster_titles": missing_high_priority_clusters,
            },
        )
    )

    signal_cluster_status = "pass"
    signal_cluster_summary = "每条主信号都绑定到单一事件簇。"
    if multi_cluster_signal_titles:
        signal_cluster_status = "fail"
        signal_cluster_summary = "有主信号把多个事件簇混在一起，简报表达过于松散。"
    elif unclustered_signal_titles:
        signal_cluster_status = "warn"
        signal_cluster_summary = "有主信号虽然挂了来源，但没有映射到当前事件簇。"
    findings.append(
        AiHotTrackerJudgmentFinding(
            code="brief_signal_cluster_consistency",
            status=signal_cluster_status,
            summary=signal_cluster_summary,
            details={
                "multi_cluster_signal_titles": multi_cluster_signal_titles,
                "unclustered_signal_titles": unclustered_signal_titles,
            },
        )
    )

    signal_priority_status = "pass"
    signal_priority_summary = "主信号的优先级与底层判断一致。"
    if overstated_priority_signals:
        signal_priority_status = "fail"
        signal_priority_summary = "有主信号在简报里夸大了优先级。"
    elif understated_priority_signals:
        signal_priority_status = "warn"
        signal_priority_summary = "有主信号在简报里压低了优先级，可能削弱重点。"
    findings.append(
        AiHotTrackerJudgmentFinding(
            code="brief_signal_priority_alignment",
            status=signal_priority_status,
            summary=signal_priority_summary,
            details={
                "overstated_signals": overstated_priority_signals,
                "understated_signals": understated_priority_signals,
            },
        )
    )

    findings.append(
        AiHotTrackerJudgmentFinding(
            code="brief_signal_change_type_alignment",
            status="pass" if not change_type_mismatches else "fail",
            summary=(
                "主信号的变化类型与底层簇状态一致。"
                if not change_type_mismatches
                else "有主信号的变化类型与底层簇状态不一致。"
            ),
            details={"mismatched_signals": change_type_mismatches},
        )
    )

    ranked_items = run.source_items
    top_ranked_item = ranked_items[0] if ranked_items else None
    strongest_official_item = next(
        (item for item in ranked_items if item.source_family == "official"),
        None,
    )
    media_overrides_official = bool(
        top_ranked_item
        and strongest_official_item
        and top_ranked_item.source_family == "media"
        and strongest_official_item.id != top_ranked_item.id
        and strongest_official_item.score_breakdown.authority >= top_ranked_item.score_breakdown.authority
        and strongest_official_item.score_breakdown.impact >= top_ranked_item.score_breakdown.impact
    )
    findings.append(
        AiHotTrackerJudgmentFinding(
            code="official_priority_guardrail",
            status="fail" if media_overrides_official else "pass",
            summary=(
                "高可信官方来源没有被精选媒体错误压过。"
                if not media_overrides_official
                else "当前排序让媒体来源压过了更高可信、影响不低的官方来源。"
            ),
            details={
                "top_ranked_item_id": top_ranked_item.id if top_ranked_item is not None else None,
                "top_ranked_source_family": (
                    top_ranked_item.source_family if top_ranked_item is not None else None
                ),
                "strongest_official_item_id": (
                    strongest_official_item.id if strongest_official_item is not None else None
                ),
            },
        )
    )

    needs_blindspots = (
        run.status in {"degraded", "failed"}
        or bool(run.source_failures)
        or any(signal.confidence == "low" for signal in run.output.signals)
    )
    blindspot_check_status = "pass"
    blindspot_summary = "本轮盲点说明与当前证据状态一致。"
    if needs_blindspots and not run.output.blindspots:
        blindspot_check_status = "fail"
        blindspot_summary = "当前证据明显不完整，但简报没有暴露盲点。"
    elif not needs_blindspots and not run.output.blindspots:
        blindspot_check_status = "warn"
        blindspot_summary = "本轮没有额外盲点，这轮判断需要人工确认是否过于乐观。"
    findings.append(
        AiHotTrackerJudgmentFinding(
            code="blindspot_honesty",
            status=blindspot_check_status,
            summary=blindspot_summary,
            details={
                "blindspot_count": len(run.output.blindspots),
                "source_failure_count": len(run.source_failures),
                "run_status": run.status,
            },
        )
    )

    active_event_ids = {cluster.event_id for cluster in clustered_signals}
    covered_active_event_ids = {
        memory.event_id
        for memory in event_memories
        if memory.event_id in active_event_ids
    }
    missing_event_memories = sorted(active_event_ids - covered_active_event_ids)
    memory_check_status = "pass" if not missing_event_memories else "warn"
    findings.append(
        AiHotTrackerJudgmentFinding(
            code="event_memory_continuity",
            status=memory_check_status,
            summary=(
                "当前活跃信号都能看到对应的事件记忆。"
                if not missing_event_memories
                else "有活跃信号没有映射到事件记忆，连续性判断可能会变弱。"
            ),
            details={
                "active_event_count": len(active_event_ids),
                "memory_event_count": len(event_memories),
                "missing_event_ids": missing_event_memories,
            },
        )
    )

    incomplete_follow_ups = [
        {
            "question": follow_up.question,
            "grounding_source_item_ids": list(follow_up.grounding_source_item_ids),
            "grounding_event_ids": list(follow_up.grounding_event_ids),
        }
        for follow_up in run.follow_ups
        if not (
            follow_up.grounding_source_item_ids
            or follow_up.grounding_event_ids
            or follow_up.grounding_blindspots
        )
    ]
    follow_up_status = "pass" if not incomplete_follow_ups else "fail"
    if not run.follow_ups:
        follow_up_status = "pass"
    findings.append(
        AiHotTrackerJudgmentFinding(
            code="follow_up_grounding_visibility",
            status=follow_up_status,
            summary=(
                "已保存追问都带有依据元数据。"
                if run.follow_ups and not incomplete_follow_ups
                else (
                    "当前还没有保存追问。"
                    if not run.follow_ups
                    else "有追问缺少依据元数据，无法检查回答到底依赖了哪些信号和来源。"
                )
            ),
            details={
                "follow_up_count": len(run.follow_ups),
                "follow_ups": [
                    {
                        "question": follow_up.question,
                        "grounding_source_item_ids": list(follow_up.grounding_source_item_ids),
                        "grounding_event_ids": list(follow_up.grounding_event_ids),
                        "grounding_blindspots": list(follow_up.grounding_blindspots),
                        "grounding_notes": list(follow_up.grounding_notes),
                    }
                    for follow_up in run.follow_ups
                ],
                "incomplete_follow_ups": incomplete_follow_ups,
            },
        )
    )

    return findings


def _finalize_report_change_state(
    *,
    report: AiHotTrackerReportResponse,
    delta: AiHotTrackerTrackingRunDelta,
) -> AiHotTrackerReportResponse:
    output = report.output.model_copy(update={"change_state": delta.change_state})
    return report.model_copy(update={"title": output.headline, "output": output})


def _execute_tracking_cycle(
    *,
    workspace: Workspace,
    actor_user_id: str,
    trigger_kind: str,
    persist_run: bool | None,
) -> _TrackingExecutionResult:
    tracking_profile = _resolve_tracking_profile(workspace.module_config_json)
    previous_snapshot, previous_saved_run_id = _load_previous_snapshot(
        workspace_id=workspace.id,
    )
    previous_memories = _load_signal_memories(workspace_id=workspace.id)
    reference_time = datetime.now(UTC)

    try:
        intake = filter_ai_hot_tracker_source_intake(
            intake=fetch_ai_hot_tracker_source_items(total_limit=tracking_profile.max_items_per_run),
            tracking_profile=tracking_profile,
        )
        decision_result = build_signal_decision_result(
            source_catalog=intake.source_catalog,
            source_items=intake.source_items,
            tracking_profile=tracking_profile,
            previous_snapshot=previous_snapshot,
            previous_memories=previous_memories,
            reference_time=reference_time,
        )
        report = generate_ai_hot_tracker_report_from_intake(
            intake=intake,
            tracking_profile=tracking_profile,
            decision_result=decision_result,
            generated_at=reference_time,
        )
        status = "degraded" if report.degraded_reason else "completed"
        delta = build_tracking_delta(
            previous_run_id=previous_saved_run_id,
            previous_snapshot=previous_snapshot,
            current_clusters=decision_result.signal_clusters,
            tracking_profile=tracking_profile,
            status=status,
            degraded_reason=report.degraded_reason,
        )
        report = _finalize_report_change_state(report=report, delta=delta)

        should_persist_run = (
            persist_run
            if persist_run is not None
            else _should_persist_scheduled_run(status=status, delta=delta)
        )
        run: AiHotTrackerTrackingRunResponse | None = None
        if should_persist_run:
            run = _persist_run(
                workspace_id=workspace.id,
                previous_run_id=previous_saved_run_id,
                user_id=actor_user_id,
                trigger_kind=trigger_kind,
                status=status,
                report=report,
                tracking_profile=tracking_profile,
                delta=delta,
            )

        _store_signal_memories(
            workspace_id=workspace.id,
            decision_result=decision_result,
            run_id=run.id if run is not None else None,
        )

        _store_tracking_state(
            workspace_id=workspace.id,
            reference_time=reference_time,
            tracking_profile=tracking_profile,
            decision_result=decision_result,
            saved_run_id=run.id if run is not None else None,
            saved_run_generated_at=run.generated_at if run is not None else None,
            notified_run_id=run.id if run is not None and delta.should_notify else None,
            latest_meaningful_update_at=(
                run.generated_at
                if run is not None and delta.change_state == "meaningful_update"
                else None
            ),
            status=status,
            error_message=report.output.summary if status == "degraded" else None,
        )
        return _TrackingExecutionResult(run=run, status=status, delta=delta)
    except Exception as error:
        report = _build_failed_report(
            tracking_profile=tracking_profile,
            generated_at=reference_time,
            error_message=str(error),
        )
        delta = build_tracking_delta(
            previous_run_id=previous_saved_run_id,
            previous_snapshot=previous_snapshot,
            current_clusters=[],
            tracking_profile=tracking_profile,
            status="failed",
        )
        report = _finalize_report_change_state(report=report, delta=delta)

        should_persist_run = (
            persist_run
            if persist_run is not None
            else _should_persist_scheduled_run(status="failed", delta=delta)
        )
        run: AiHotTrackerTrackingRunResponse | None = None
        if should_persist_run:
            run = _persist_run(
                workspace_id=workspace.id,
                previous_run_id=previous_saved_run_id,
                user_id=actor_user_id,
                trigger_kind=trigger_kind,
                status="failed",
                report=report,
                tracking_profile=tracking_profile,
                delta=delta,
                error_message=str(error),
            )

        _store_tracking_state(
            workspace_id=workspace.id,
            reference_time=reference_time,
            tracking_profile=tracking_profile,
            decision_result=None,
            saved_run_id=run.id if run is not None else None,
            saved_run_generated_at=run.generated_at if run is not None else None,
            notified_run_id=None,
            latest_meaningful_update_at=None,
            status="failed",
            error_message=str(error),
        )
        return _TrackingExecutionResult(run=run, status="failed", delta=delta)


def _is_workspace_due_for_scan(
    *,
    workspace_id: str,
    tracking_profile: AiHotTrackerTrackingProfile,
    reference_time: datetime,
) -> bool:
    if tracking_profile.cadence == "manual":
        return False

    tracking_state = ai_hot_tracker_tracking_state_repository.get_ai_hot_tracker_tracking_state(
        workspace_id=workspace_id
    )
    if tracking_state is None:
        return True
    if tracking_state.next_due_at is not None:
        return _normalize_datetime(tracking_state.next_due_at) <= reference_time
    interval = _CADENCE_INTERVALS.get(tracking_profile.cadence)
    last_checked_at = _normalize_datetime(tracking_state.last_checked_at)
    if interval is None or last_checked_at is None:
        return True
    return last_checked_at + interval <= reference_time


def _resolve_latest_saved_run(
    workspace_id: str,
    state_last_saved_run_id: str | None,
) -> AiHotTrackerTrackingRunResponse | None:
    if state_last_saved_run_id:
        run = ai_hot_tracker_tracking_run_repository.get_ai_hot_tracker_tracking_run(
            run_id=state_last_saved_run_id
        )
        if run is not None:
            return AiHotTrackerTrackingRunResponse.from_model(run)
    return _load_previous_run(workspace_id)


def _load_signal_clusters_from_run(
    run: AiHotTrackerTrackingRunResponse,
) -> list[AiHotTrackerSignalCluster]:
    raw_clusters = run.source_set.get("signal_clusters") if isinstance(run.source_set, dict) else None
    if isinstance(raw_clusters, list):
        return [
            AiHotTrackerSignalCluster.model_validate(item)
            for item in raw_clusters
            if isinstance(item, dict)
        ]
    decision_result = build_signal_decision_result(
        source_catalog=run.source_catalog,
        source_items=run.source_items,
        tracking_profile=run.profile,
        previous_snapshot=None,
        reference_time=run.generated_at,
    )
    return decision_result.signal_clusters


def _load_event_memories_from_run(
    run: AiHotTrackerTrackingRunResponse,
) -> list[AiHotTrackerSignalMemoryRecord]:
    raw_memories = run.source_set.get("event_memories") if isinstance(run.source_set, dict) else None
    if isinstance(raw_memories, list):
        return [
            AiHotTrackerSignalMemoryRecord.model_validate(item)
            for item in raw_memories
            if isinstance(item, dict)
        ]

    return [
        memory
        for memory in _load_signal_memories(workspace_id=run.workspace_id)
        if any(
            item.event_id == memory.event_id
            for item in _load_signal_clusters_from_run(run)
        )
    ]


def _load_agent_trace_from_run(
    run: AiHotTrackerTrackingRunResponse,
) -> list[AiHotTrackerAgentRoleTrace]:
    raw_trace = run.source_set.get("agent_trace") if isinstance(run.source_set, dict) else None
    trace: list[AiHotTrackerAgentRoleTrace] = []
    if isinstance(raw_trace, list):
        trace.extend(
            AiHotTrackerAgentRoleTrace.model_validate(item)
            for item in raw_trace
            if isinstance(item, dict)
        )
    trace.append(
        AiHotTrackerAgentRoleTrace(
            role="editor",
            summary=(
                f"本轮产出 {len(run.output.signals)} 条主信号、"
                f"{len(run.output.keep_watching)} 条继续观察，"
                f"{len(run.output.blindspots)} 条盲点提示。"
            ),
            status="degraded" if run.degraded_reason else "completed",
            details={
                "signal_count": len(run.output.signals),
                "keep_watching_count": len(run.output.keep_watching),
                "blindspot_count": len(run.output.blindspots),
            },
        )
    )
    trace.append(
        AiHotTrackerAgentRoleTrace(
            role="evaluator",
            summary=(
                "本轮已形成重要变化判断。"
                if run.delta.change_state in {"first_run", "meaningful_update"}
                else "本轮判断为平稳或降级状态。"
            ),
            status="failed" if run.status == "failed" else ("degraded" if run.status == "degraded" else "completed"),
            details={
                "change_state": run.delta.change_state,
                "priority_level": run.delta.priority_level,
                "notify_reason": run.delta.notify_reason,
                "source_failure_count": len(run.source_failures),
            },
        )
    )
    if run.follow_ups:
        trace.append(
            AiHotTrackerAgentRoleTrace(
                role="follow_up",
                summary=f"当前这份简报已经承接 {len(run.follow_ups)} 轮追问。",
                status="completed",
                details={"follow_up_count": len(run.follow_ups)},
            )
        )
    return trace


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
    result = _execute_tracking_cycle(
        workspace=workspace,
        actor_user_id=user_id,
        trigger_kind=request.trigger_kind,
        persist_run=True,
    )
    if result.run is None:
        raise AiHotTrackerTrackingAccessError("Manual tracking run did not persist a result")
    return result.run


def run_ai_hot_tracker_tracking_sweeper() -> dict[str, object]:
    reference_time = datetime.now(UTC)
    checked_workspace_count = 0
    processed_workspace_count = 0
    saved_run_count = 0

    for workspace in workspace_repository.list_workspaces_by_module_type("research"):
        tracking_profile = _resolve_tracking_profile(workspace.module_config_json)
        if not _is_workspace_due_for_scan(
            workspace_id=workspace.id,
            tracking_profile=tracking_profile,
            reference_time=reference_time,
        ):
            continue

        checked_workspace_count += 1
        result = _execute_tracking_cycle(
            workspace=workspace,
            actor_user_id=workspace.owner_id,
            trigger_kind="scheduled",
            persist_run=None,
        )
        processed_workspace_count += 1
        if result.run is not None:
            saved_run_count += 1

    return {
        "checked_workspace_count": checked_workspace_count,
        "processed_workspace_count": processed_workspace_count,
        "saved_run_count": saved_run_count,
        "swept_at": reference_time.isoformat(),
    }


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


def get_ai_hot_tracker_tracking_state(
    *,
    workspace_id: str,
    user_id: str,
) -> AiHotTrackerTrackingStateResponse:
    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        raise AiHotTrackerTrackingAccessError("Workspace not found")
    if workspace.module_type != "research":
        raise AiHotTrackerTrackingAccessError("AI hot tracker is only available in research workspaces")

    tracking_profile = _resolve_tracking_profile(workspace.module_config_json)
    tracking_state = ai_hot_tracker_tracking_state_repository.get_ai_hot_tracker_tracking_state(
        workspace_id=workspace_id
    )
    latest_run = _resolve_latest_saved_run(
        workspace_id=workspace_id,
        state_last_saved_run_id=(
            tracking_state.last_saved_run_id if tracking_state is not None else None
        ),
    )

    return AiHotTrackerTrackingStateResponse(
        workspace_id=workspace_id,
        tracking_profile=tracking_profile,
        last_checked_at=(tracking_state.last_checked_at if tracking_state is not None else None),
        last_successful_scan_at=(
            tracking_state.last_successful_scan_at if tracking_state is not None else None
        ),
        next_due_at=(tracking_state.next_due_at if tracking_state is not None else None),
        consecutive_failure_count=(
            tracking_state.consecutive_failure_count if tracking_state is not None else 0
        ),
        last_error_message=(tracking_state.last_error_message if tracking_state is not None else None),
        latest_saved_run_id=(latest_run.id if latest_run is not None else None),
        latest_saved_run_generated_at=(
            tracking_state.latest_saved_run_generated_at
            if tracking_state is not None and tracking_state.latest_saved_run_generated_at is not None
            else (latest_run.generated_at if latest_run is not None else None)
        ),
        latest_change_state=(latest_run.delta.change_state if latest_run is not None else None),
        latest_notify_reason=(latest_run.delta.notify_reason if latest_run is not None else None),
        latest_meaningful_update_at=(
            tracking_state.latest_meaningful_update_at if tracking_state is not None else None
        ),
    )


def get_ai_hot_tracker_run_evaluation(
    *,
    run_id: str,
    user_id: str,
) -> AiHotTrackerRunEvaluationResponse:
    run = get_ai_hot_tracker_tracking_run(run_id=run_id, user_id=user_id)
    if run is None:
        raise AiHotTrackerTrackingAccessError("AI hot tracker run not found")

    clustered_signals = _load_signal_clusters_from_run(run)
    event_memories = _load_event_memories_from_run(run)
    quality_checks = _build_run_quality_checks(
        run=run,
        clustered_signals=clustered_signals,
        event_memories=event_memories,
    )
    judgment_findings, brief_alignment_checks, follow_up_grounding_checks = (
        _partition_run_quality_checks(quality_checks)
    )

    return AiHotTrackerRunEvaluationResponse(
        run_id=run.id,
        ranked_items=run.source_items,
        clustered_signals=clustered_signals,
        event_memories=event_memories,
        source_failures=run.source_failures,
        output=run.output,
        delta=run.delta,
        agent_trace=_load_agent_trace_from_run(run),
        quality_checks=quality_checks,
        judgment_findings=judgment_findings,
        brief_alignment_checks=brief_alignment_checks,
        follow_up_grounding_checks=follow_up_grounding_checks,
    )


def delete_ai_hot_tracker_tracking_run(*, run_id: str, user_id: str) -> bool:
    run = get_ai_hot_tracker_tracking_run(run_id=run_id, user_id=user_id)
    deleted = ai_hot_tracker_tracking_run_repository.delete_ai_hot_tracker_tracking_run(
        run_id=run_id,
        user_id=user_id,
    )
    if not deleted or run is None:
        return deleted

    tracking_state = ai_hot_tracker_tracking_state_repository.get_ai_hot_tracker_tracking_state(
        workspace_id=run.workspace_id
    )
    if tracking_state is None:
        return True

    latest_remaining_run = _load_previous_run(run.workspace_id)
    latest_meaningful_update_at = tracking_state.latest_meaningful_update_at
    if latest_meaningful_update_at == run.generated_at:
        latest_meaningful_update_at = None

    ai_hot_tracker_tracking_state_repository.upsert_ai_hot_tracker_tracking_state(
        workspace_id=tracking_state.workspace_id,
        last_checked_at=tracking_state.last_checked_at,
        last_evaluated_at=tracking_state.last_evaluated_at,
        last_successful_scan_at=tracking_state.last_successful_scan_at,
        next_due_at=tracking_state.next_due_at,
        last_cluster_snapshot_json=tracking_state.last_cluster_snapshot_json,
        last_saved_run_id=(
            latest_remaining_run.id
            if tracking_state.last_saved_run_id == run_id and latest_remaining_run is not None
            else (None if tracking_state.last_saved_run_id == run_id else tracking_state.last_saved_run_id)
        ),
        latest_saved_run_generated_at=(
            latest_remaining_run.generated_at
            if tracking_state.last_saved_run_id == run_id and latest_remaining_run is not None
            else (
                None
                if tracking_state.last_saved_run_id == run_id
                else tracking_state.latest_saved_run_generated_at
            )
        ),
        last_notified_run_id=(
            None if tracking_state.last_notified_run_id == run_id else tracking_state.last_notified_run_id
        ),
        latest_meaningful_update_at=latest_meaningful_update_at,
        consecutive_failure_count=tracking_state.consecutive_failure_count,
        last_error_message=tracking_state.last_error_message,
    )
    return True


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
        response = answer_ai_hot_tracker_tracking_run_follow_up(run=run, payload=payload)
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

