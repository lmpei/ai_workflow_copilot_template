from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse

from app.schemas.ai_frontier_research import (
    AiHotTrackerAgentRoleTrace,
    AiHotTrackerClusterSnapshot,
    AiHotTrackerPriorityLevel,
    AiHotTrackerScoreBreakdown,
    AiHotTrackerSignalCluster,
    AiHotTrackerSignalMemoryRecord,
    AiHotTrackerSourceDefinition,
    AiHotTrackerSourceItem,
    AiHotTrackerTrackingProfile,
    AiHotTrackerTrackingRunDelta,
)

HIGH_PRIORITY_THRESHOLD = 0.80
MEDIUM_PRIORITY_THRESHOLD = 0.60
MAX_REPORT_CANDIDATE_CLUSTERS = 8
MIN_REPORT_PRIMARY_CLUSTERS = 4
_TITLE_MATCH_WINDOW = timedelta(days=7)
_ENTITY_MATCH_WINDOW = timedelta(days=10)
_WORD_PATTERN = re.compile(r"[a-z0-9][a-z0-9._/-]*")
_VERSION_PATTERN = re.compile(r"^v?\d+(?:\.\d+){1,4}(?:[-._a-z0-9]+)?$")
_DATE_PATTERN = re.compile(r"^\d{4}([-/]\d{1,2}){1,2}$")
_STOPWORDS = {
    "a",
    "ai",
    "an",
    "and",
    "for",
    "from",
    "in",
    "into",
    "new",
    "news",
    "of",
    "on",
    "release",
    "released",
    "the",
    "to",
    "update",
    "with",
}
_HIGH_IMPACT_TOKENS = {
    "agent",
    "agents",
    "api",
    "benchmark",
    "browser",
    "chatgpt",
    "claude",
    "copilot",
    "desktop",
    "developer",
    "gemini",
    "gpt",
    "image",
    "launch",
    "model",
    "multimodal",
    "open",
    "reasoning",
    "release",
    "research",
    "tool",
    "video",
    "voice",
}
_KNOWN_ENTITIES = {
    "anthropic": {"anthropic", "claude"},
    "deepmind": {"deepmind"},
    "gemini": {"gemini"},
    "google": {"google", "notebooklm"},
    "huggingface": {"huggingface", "hugging", "transformers"},
    "langchain": {"langchain", "langgraph"},
    "llama": {"llama"},
    "meta": {"meta"},
    "mistral": {"mistral"},
    "ollama": {"ollama"},
    "openai": {"openai", "chatgpt", "gpt"},
    "vllm": {"vllm"},
}
_PRIORITY_ORDER: dict[AiHotTrackerPriorityLevel, int] = {
    "low": 0,
    "medium": 1,
    "high": 2,
}


@dataclass(slots=True)
class AiHotTrackerDecisionResult:
    source_items: list[AiHotTrackerSourceItem]
    signal_clusters: list[AiHotTrackerSignalCluster]
    candidate_clusters: list[AiHotTrackerSignalCluster]
    cluster_snapshot: list[AiHotTrackerClusterSnapshot]
    signal_memories: list[AiHotTrackerSignalMemoryRecord]
    agent_trace: list[AiHotTrackerAgentRoleTrace] = field(default_factory=list)


@dataclass(slots=True)
class _ItemFeatures:
    item: AiHotTrackerSourceItem
    repo_slug: str | None
    canonical_url_stem: str
    title_fingerprint: str
    entity_fingerprint: str | None
    title_tokens: list[str]
    version_tokens: list[str]
    core_tokens: list[str]


@dataclass(slots=True)
class _ClusterDraft:
    category: str
    fingerprint: str
    repo_slug: str | None
    canonical_url_stem: str | None
    title_fingerprint: str
    entity_fingerprint: str | None
    items: list[_ItemFeatures] = field(default_factory=list)

    @property
    def representative_published_at(self) -> datetime | None:
        if not self.items:
            return None
        return max(
            (feature.item.published_at for feature in self.items if feature.item.published_at is not None),
            default=None,
        )


def deserialize_cluster_snapshot(
    value: object,
) -> list[AiHotTrackerClusterSnapshot]:
    if not isinstance(value, list):
        return []
    return [
        AiHotTrackerClusterSnapshot.model_validate(item)
        for item in value
        if isinstance(item, dict)
    ]


def build_signal_decision_result(
    *,
    source_catalog: list[AiHotTrackerSourceDefinition],
    source_items: list[AiHotTrackerSourceItem],
    tracking_profile: AiHotTrackerTrackingProfile,
    previous_snapshot: list[AiHotTrackerClusterSnapshot] | None = None,
    previous_memories: list[AiHotTrackerSignalMemoryRecord] | None = None,
    reference_time: datetime | None = None,
) -> AiHotTrackerDecisionResult:
    evaluated_at = reference_time or datetime.now(UTC)
    authority_by_source = {source.id: source.authority_weight for source in source_catalog}
    previous_snapshot_map = {
        snapshot.cluster_id: snapshot
        for snapshot in previous_snapshot or []
    }
    previous_memory_by_event = {
        memory.event_id: memory
        for memory in previous_memories or []
    }
    previous_memory_by_fingerprint = {
        memory.fingerprint: memory
        for memory in previous_memories or []
    }

    features = [_build_item_features(item) for item in source_items]
    clusters = _cluster_items(features)
    scored_items_by_id: dict[str, AiHotTrackerSourceItem] = {}
    signal_clusters: list[AiHotTrackerSignalCluster] = []

    for cluster in clusters:
        cluster_id = _build_cluster_id(cluster.category, cluster.fingerprint)
        event_id = _build_event_id(cluster.category, cluster.fingerprint)
        previous_cluster = previous_snapshot_map.get(cluster_id)
        previous_memory = previous_memory_by_event.get(event_id) or previous_memory_by_fingerprint.get(
            cluster.fingerprint
        )
        cluster_items: list[AiHotTrackerSourceItem] = []
        for feature in cluster.items:
            scored_item = _score_source_item(
                feature=feature,
                cluster=cluster,
                previous_cluster=previous_cluster,
                previous_memory=previous_memory,
                authority_by_source=authority_by_source,
                tracking_profile=tracking_profile,
                evaluated_at=evaluated_at,
            )
            scored_items_by_id[scored_item.id] = scored_item
            cluster_items.append(scored_item)

        representative = _pick_representative_item(cluster_items)
        priority_level = _resolve_priority_level(representative.rank_score)
        signal_clusters.append(
            AiHotTrackerSignalCluster(
                cluster_id=representative.cluster_id or cluster_id,
                event_id=representative.event_id or event_id,
                title=representative.title,
                category=cluster.category,
                representative_item_id=representative.id,
                source_item_ids=[item.id for item in cluster_items],
                source_labels=_unique_in_order(item.source_label for item in cluster_items),
                rank_score=round(representative.rank_score, 4),
                priority_level=priority_level,
                fingerprint=cluster.fingerprint,
                is_new=previous_memory is None,
                is_continuing=previous_memory is not None,
                is_cooling=False,
            )
        )

    ordered_items = sorted(
        scored_items_by_id.values(),
        key=lambda item: (
            item.rank_score,
            item.published_at or datetime.min.replace(tzinfo=UTC),
        ),
        reverse=True,
    )
    ordered_clusters = sorted(
        signal_clusters,
        key=lambda cluster: (
            cluster.rank_score,
            cluster.priority_level == "high",
            cluster.priority_level == "medium",
        ),
        reverse=True,
    )
    candidate_clusters = select_report_candidate_clusters(ordered_clusters)
    cluster_snapshot = [
        _build_cluster_snapshot(cluster=cluster, scored_items_by_id=scored_items_by_id)
        for cluster in ordered_clusters
    ]
    signal_memories = _build_signal_memory_records(
        current_clusters=ordered_clusters,
        scored_items_by_id=scored_items_by_id,
        previous_memories=previous_memories or [],
        evaluated_at=evaluated_at,
    )

    return AiHotTrackerDecisionResult(
        source_items=ordered_items,
        signal_clusters=ordered_clusters,
        candidate_clusters=candidate_clusters,
        cluster_snapshot=cluster_snapshot,
        signal_memories=signal_memories,
        agent_trace=[
            AiHotTrackerAgentRoleTrace(
                role="resolver",
                summary=(
                    f"本轮把 {len(source_items)} 条来源条目收敛成 "
                    f"{len(ordered_clusters)} 个可读信号。"
                ),
                status="completed",
                details={
                    "source_item_count": len(source_items),
                    "cluster_count": len(ordered_clusters),
                },
            ),
            AiHotTrackerAgentRoleTrace(
                role="analyst",
                summary=(
                    f"本轮保留 {len(candidate_clusters)} 个简报候选，"
                    f"并更新 {len(signal_memories)} 条事件记忆。"
                ),
                status="completed",
                details={
                    "candidate_cluster_count": len(candidate_clusters),
                    "event_memory_count": len(signal_memories),
                },
            ),
        ],
    )

def build_tracking_delta(
    *,
    previous_run_id: str | None,
    previous_snapshot: list[AiHotTrackerClusterSnapshot] | None,
    current_clusters: list[AiHotTrackerSignalCluster],
    tracking_profile: AiHotTrackerTrackingProfile,
    status: str,
    degraded_reason: str | None = None,
) -> AiHotTrackerTrackingRunDelta:
    previous_cluster_map = {
        snapshot.cluster_id: snapshot
        for snapshot in previous_snapshot or []
    }
    current_cluster_map = {cluster.cluster_id: cluster for cluster in current_clusters}

    new_clusters = [
        cluster
        for cluster in current_clusters
        if cluster.cluster_id not in previous_cluster_map
    ]
    continuing_clusters = [
        cluster
        for cluster in current_clusters
        if cluster.cluster_id in previous_cluster_map
    ]
    cooled_clusters = [
        snapshot
        for snapshot in previous_snapshot or []
        if snapshot.cluster_id not in current_cluster_map
    ]

    common_payload = {
        "previous_run_id": previous_run_id,
        "new_item_count": len(new_clusters),
        "continuing_item_count": len(continuing_clusters),
        "cooled_down_item_count": len(cooled_clusters),
        "new_titles": [cluster.title for cluster in new_clusters[:4]],
        "continuing_titles": [cluster.title for cluster in continuing_clusters[:4]],
        "cooled_down_titles": [cluster.title for cluster in cooled_clusters[:4]],
    }

    if status == "failed":
        return AiHotTrackerTrackingRunDelta(
            **common_payload,
            change_state="failed",
            summary="本轮追踪运行失败，未形成可用判断。",
            should_notify=False,
            priority_level="low",
            notify_reason=None,
        )

    if degraded_reason:
        return AiHotTrackerTrackingRunDelta(
            **common_payload,
            change_state="degraded",
            summary="来源已经更新，但本轮结构化判断不完整。",
            should_notify=False,
            priority_level=_max_priority_level(cluster.priority_level for cluster in current_clusters),
            notify_reason=None,
        )

    if not previous_snapshot:
        return AiHotTrackerTrackingRunDelta(
            **common_payload,
            change_state="first_run",
            summary="首次形成有效追踪结果，后续轮次将开始比较变化。",
            should_notify=True,
            priority_level=_max_priority_level(cluster.priority_level for cluster in current_clusters),
            notify_reason="首次形成有效追踪结果",
        )

    new_high_clusters = [cluster for cluster in new_clusters if cluster.priority_level == "high"]
    new_medium_or_above_clusters = [
        cluster for cluster in new_clusters if cluster.priority_level in {"high", "medium"}
    ]

    if new_high_clusters:
        return AiHotTrackerTrackingRunDelta(
            **common_payload,
            change_state="meaningful_update",
            summary=(
                f"本轮发现 {len(new_high_clusters)} 个高优先级新信号，"
                f"并有 {len(continuing_clusters)} 个信号仍在延续。"
            ),
            should_notify=True,
            priority_level="high",
            notify_reason="发现高优先级新增信号",
        )

    if len(new_medium_or_above_clusters) >= tracking_profile.alert_threshold:
        return AiHotTrackerTrackingRunDelta(
            **common_payload,
            change_state="meaningful_update",
            summary=(
                f"本轮新增 {len(new_medium_or_above_clusters)} 个中高优先级信号，"
                f"达到当前提醒阈值 {tracking_profile.alert_threshold}。"
            ),
            should_notify=True,
            priority_level=_max_priority_level(
                cluster.priority_level for cluster in new_medium_or_above_clusters
            ),
            notify_reason=(
                f"新增中高优先级信号达到阈值 {tracking_profile.alert_threshold}"
            ),
        )

    return AiHotTrackerTrackingRunDelta(
        **common_payload,
        change_state="steady_state",
        summary=(
            f"本轮没有达到提醒阈值的新增变化，"
            f"当前延续 {len(continuing_clusters)} 个信号，降温 {len(cooled_clusters)} 个信号。"
        ),
        should_notify=False,
        priority_level=_max_priority_level(cluster.priority_level for cluster in current_clusters),
        notify_reason=None,
    )

def select_report_candidate_clusters(
    signal_clusters: list[AiHotTrackerSignalCluster],
) -> list[AiHotTrackerSignalCluster]:
    primary_clusters = [
        cluster for cluster in signal_clusters if cluster.priority_level in {"high", "medium"}
    ]
    selected = primary_clusters[:MAX_REPORT_CANDIDATE_CLUSTERS]
    if len(selected) >= MIN_REPORT_PRIMARY_CLUSTERS:
        return selected

    selected_ids = {cluster.cluster_id for cluster in selected}
    for cluster in signal_clusters:
        if cluster.cluster_id in selected_ids:
            continue
        selected.append(cluster)
        selected_ids.add(cluster.cluster_id)
        if len(selected) >= min(
            MAX_REPORT_CANDIDATE_CLUSTERS,
            max(MIN_REPORT_PRIMARY_CLUSTERS, len(signal_clusters)),
        ):
            break
    return selected[:MAX_REPORT_CANDIDATE_CLUSTERS]


def _build_item_features(item: AiHotTrackerSourceItem) -> _ItemFeatures:
    title_tokens = _tokenize(item.title)
    summary_tokens = _tokenize(item.summary)
    source_tokens = _tokenize(f"{item.source_label} {item.url}")
    all_tokens = title_tokens + summary_tokens + source_tokens + [
        token.casefold() for token in item.tags
    ]
    version_tokens = [token for token in title_tokens if _is_version_token(token)]
    core_tokens = [
        token for token in title_tokens if token not in _STOPWORDS and not _is_version_token(token)
    ]
    title_fingerprint = " ".join(sorted(dict.fromkeys(core_tokens)))
    entity_fingerprint = _extract_entity_fingerprint(all_tokens)
    return _ItemFeatures(
        item=item,
        repo_slug=_extract_repo_slug(item.url),
        canonical_url_stem=_build_canonical_url_stem(item.url),
        title_fingerprint=title_fingerprint,
        entity_fingerprint=entity_fingerprint,
        title_tokens=title_tokens,
        version_tokens=version_tokens,
        core_tokens=core_tokens,
    )


def _cluster_items(features: list[_ItemFeatures]) -> list[_ClusterDraft]:
    ordered_features = sorted(
        features,
        key=lambda feature: feature.item.published_at or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )
    clusters: list[_ClusterDraft] = []
    for feature in ordered_features:
        matched_cluster = next(
            (cluster for cluster in clusters if _feature_matches_cluster(feature, cluster)),
            None,
        )
        if matched_cluster is None:
            fingerprint = _build_cluster_fingerprint(feature)
            clusters.append(
                _ClusterDraft(
                    category=feature.item.category,
                    fingerprint=fingerprint,
                    repo_slug=feature.repo_slug,
                    canonical_url_stem=feature.canonical_url_stem,
                    title_fingerprint=feature.title_fingerprint,
                    entity_fingerprint=feature.entity_fingerprint,
                    items=[feature],
                )
            )
            continue
        matched_cluster.items.append(feature)
    return clusters


def _feature_matches_cluster(feature: _ItemFeatures, cluster: _ClusterDraft) -> bool:
    same_category = feature.item.category == cluster.category
    if same_category and feature.repo_slug and feature.repo_slug == cluster.repo_slug:
        return True
    if same_category and feature.canonical_url_stem == cluster.canonical_url_stem:
        return True
    if same_category and feature.title_fingerprint and feature.title_fingerprint == cluster.title_fingerprint:
        return _published_within_window(feature, cluster, _TITLE_MATCH_WINDOW)

    if not feature.entity_fingerprint or feature.entity_fingerprint != cluster.entity_fingerprint:
        return False
    if not _published_within_window(feature, cluster, _ENTITY_MATCH_WINDOW):
        return False
    return _token_overlap_ratio(feature.core_tokens, cluster.title_fingerprint.split()) >= 0.45


def _published_within_window(
    feature: _ItemFeatures,
    cluster: _ClusterDraft,
    window: timedelta,
) -> bool:
    representative_published_at = cluster.representative_published_at
    if representative_published_at is None or feature.item.published_at is None:
        return False
    return abs(representative_published_at - feature.item.published_at) <= window


def _build_cluster_fingerprint(feature: _ItemFeatures) -> str:
    if feature.repo_slug:
        return f"repo:{feature.repo_slug}"
    if feature.entity_fingerprint and feature.title_fingerprint:
        return f"entity:{feature.entity_fingerprint}:{feature.title_fingerprint}"
    if feature.canonical_url_stem:
        return f"url:{feature.canonical_url_stem}"
    if feature.title_fingerprint:
        return f"title:{feature.item.category}:{feature.title_fingerprint}"
    return f"item:{feature.item.source_id}:{feature.item.url.lower()}"


def _build_cluster_id(category: str, fingerprint: str) -> str:
    digest = hashlib.sha1(f"{category}:{fingerprint}".encode("utf-8")).hexdigest()
    return f"cluster-{digest[:12]}"


def _build_event_id(category: str, fingerprint: str) -> str:
    digest = hashlib.sha1(f"event:{category}:{fingerprint}".encode("utf-8")).hexdigest()
    return f"event-{digest[:12]}"


def _build_signal_memory_records(
    *,
    current_clusters: list[AiHotTrackerSignalCluster],
    scored_items_by_id: dict[str, AiHotTrackerSourceItem],
    previous_memories: list[AiHotTrackerSignalMemoryRecord],
    evaluated_at: datetime,
) -> list[AiHotTrackerSignalMemoryRecord]:
    current_by_event = {cluster.event_id: cluster for cluster in current_clusters}
    previous_by_event = {memory.event_id: memory for memory in previous_memories}
    next_records: list[AiHotTrackerSignalMemoryRecord] = []

    for cluster in current_clusters:
        existing = previous_by_event.get(cluster.event_id)
        cluster_items = [
            item
            for item_id in cluster.source_item_ids
            if (item := scored_items_by_id.get(item_id)) is not None
        ]
        source_families = _unique_in_order(item.source_family for item in cluster_items)
        streak_count = (
            1
            if existing is None or existing.activity_state in {"cooling", "replaced"}
            else existing.streak_count + 1
        )
        is_reheated = existing is not None and existing.activity_state in {"cooling", "replaced"}
        activity_state = (
            "heating"
            if (cluster.is_new and cluster.priority_level in {"high", "medium"}) or is_reheated
            else "continuing"
        )
        note = (
            "新信号正在升温，需要继续确认后续来源和真实影响。"
            if cluster.is_new and cluster.priority_level in {"high", "medium"}
            else (
                "这条信号重新回到视野，说明它还在继续发酵。"
                if is_reheated
                else "当前信号仍在延续，可继续观察后续版本、反馈或跟进。"
            )
        )
        next_records.append(
            AiHotTrackerSignalMemoryRecord(
                event_id=cluster.event_id,
                fingerprint=cluster.fingerprint,
                title=cluster.title,
                category=cluster.category,
                first_seen_at=(existing.first_seen_at if existing is not None else evaluated_at),
                last_seen_at=evaluated_at,
                continuity_state="new" if existing is None else "continuing",
                activity_state=activity_state,
                source_families=source_families,
                source_item_ids=list(cluster.source_item_ids),
                source_labels=list(cluster.source_labels),
                latest_priority_level=cluster.priority_level,
                latest_rank_score=cluster.rank_score,
                last_seen_run_id=existing.last_seen_run_id if existing is not None else None,
                streak_count=streak_count,
                cooling_since=None,
                superseded_by_event_id=None,
                last_cluster_snapshot={
                    "cluster_id": cluster.cluster_id,
                    "event_id": cluster.event_id,
                    "fingerprint": cluster.fingerprint,
                    "title": cluster.title,
                    "category": cluster.category,
                    "source_item_ids": list(cluster.source_item_ids),
                    "source_labels": list(cluster.source_labels),
                    "rank_score": cluster.rank_score,
                    "priority_level": cluster.priority_level,
                    "title_tokens": _tokenize(cluster.title),
                    "version_tokens": [
                        token for token in _tokenize(cluster.title) if _is_version_token(token)
                    ],
                },
                note=note,
            )
        )

    for memory in previous_memories:
        if memory.event_id in current_by_event:
            continue
        superseded_by_event_id = _resolve_superseding_event_id(
            memory=memory,
            current_clusters=current_clusters,
        )
        was_replaced = superseded_by_event_id is not None
        next_records.append(
            memory.model_copy(
                update={
                    "continuity_state": "cooling",
                    "activity_state": "replaced" if was_replaced else "cooling",
                    "cooling_since": memory.cooling_since or evaluated_at,
                    "superseded_by_event_id": superseded_by_event_id,
                    "note": (
                        "这条历史信号已被新的相关事件替代，转入替代观察。"
                        if was_replaced
                        else "这一条历史信号本轮没有继续出现，暂时进入降温观察。"
                    ),
                }
            )
        )

    return sorted(next_records, key=lambda memory: memory.last_seen_at, reverse=True)


def _resolve_superseding_event_id(
    *,
    memory: AiHotTrackerSignalMemoryRecord,
    current_clusters: list[AiHotTrackerSignalCluster],
) -> str | None:
    snapshot = memory.last_cluster_snapshot if isinstance(memory.last_cluster_snapshot, dict) else {}
    previous_title_tokens = [
        str(token)
        for token in snapshot.get("title_tokens", [])
        if isinstance(token, str)
    ] or _tokenize(memory.title)
    previous_version_tokens = {
        str(token)
        for token in snapshot.get("version_tokens", [])
        if isinstance(token, str)
    }
    previous_anchor = _resolve_signal_anchor(memory.fingerprint)

    for cluster in current_clusters:
        if cluster.event_id == memory.event_id or cluster.category != memory.category:
            continue

        current_anchor = _resolve_signal_anchor(cluster.fingerprint)
        current_title_tokens = _tokenize(cluster.title)
        similarity = _token_overlap_ratio(previous_title_tokens, current_title_tokens)
        current_version_tokens = {
            token for token in current_title_tokens if _is_version_token(token)
        }

        if cluster.fingerprint == memory.fingerprint:
            return cluster.event_id
        if previous_anchor is not None and previous_anchor == current_anchor and similarity >= 0.35:
            return cluster.event_id
        if previous_version_tokens and current_version_tokens and previous_version_tokens != current_version_tokens:
            if similarity >= 0.3:
                return cluster.event_id
        if similarity >= 0.78:
            return cluster.event_id

    return None


def _resolve_signal_anchor(fingerprint: str) -> str | None:
    if fingerprint.startswith("repo:"):
        return fingerprint
    if fingerprint.startswith("entity:"):
        parts = fingerprint.split(":")
        if len(parts) >= 2:
            return f"entity:{parts[1]}"
    return None

def _score_source_item(
    *,
    feature: _ItemFeatures,
    cluster: _ClusterDraft,
    previous_cluster: AiHotTrackerClusterSnapshot | None,
    previous_memory: AiHotTrackerSignalMemoryRecord | None,
    authority_by_source: dict[str, float],
    tracking_profile: AiHotTrackerTrackingProfile,
    evaluated_at: datetime,
) -> AiHotTrackerSourceItem:
    novelty_score = _build_novelty_score(
        feature=feature,
        previous_cluster=previous_cluster,
        previous_memory=previous_memory,
    )
    freshness_score = _build_freshness_score(feature.item.published_at, evaluated_at)
    authority_score = authority_by_source.get(feature.item.source_id, 0.5)
    relevance_score = _build_relevance_score(feature=feature, tracking_profile=tracking_profile)
    impact_score = _build_impact_score(feature=feature)
    rank_score = round(
        (0.30 * impact_score)
        + (0.25 * novelty_score)
        + (0.20 * freshness_score)
        + (0.15 * authority_score)
        + (0.10 * relevance_score),
        4,
    )
    cluster_id = _build_cluster_id(cluster.category, cluster.fingerprint)
    event_id = _build_event_id(cluster.category, cluster.fingerprint)
    return feature.item.model_copy(
        update={
            "cluster_id": cluster_id,
            "event_id": event_id,
            "rank_score": rank_score,
            "score_breakdown": AiHotTrackerScoreBreakdown(
                novelty=novelty_score,
                freshness=freshness_score,
                authority=authority_score,
                relevance=relevance_score,
                impact=impact_score,
            ),
            "rank_reason": _build_rank_reason(
                novelty_score=novelty_score,
                freshness_score=freshness_score,
                authority_score=authority_score,
                relevance_score=relevance_score,
                impact_score=impact_score,
            ),
        }
    )


def _build_novelty_score(
    *,
    feature: _ItemFeatures,
    previous_cluster: AiHotTrackerClusterSnapshot | None,
    previous_memory: AiHotTrackerSignalMemoryRecord | None,
) -> float:
    if previous_memory is None and previous_cluster is None:
        return 1.0
    previous_versions: set[str] = set()
    if previous_memory is not None:
        snapshot = previous_memory.last_cluster_snapshot
        if isinstance(snapshot, dict):
            previous_versions = {
                str(token)
                for token in snapshot.get("version_tokens", [])
                if isinstance(token, str)
            }
    if previous_cluster is None:
        previous_versions = previous_versions or set()
    else:
        previous_versions = previous_versions or set(previous_cluster.version_tokens)
    current_versions = set(feature.version_tokens)
    if current_versions and current_versions != previous_versions:
        return 0.65
    if previous_cluster is not None and previous_cluster.title.strip().casefold() != feature.item.title.strip().casefold():
        return 0.65
    if previous_memory is not None and previous_memory.title.strip().casefold() != feature.item.title.strip().casefold():
        return 0.65
    return 0.25


def _build_freshness_score(published_at: datetime | None, evaluated_at: datetime) -> float:
    if published_at is None:
        return 0.2
    age = evaluated_at - published_at
    if age <= timedelta(days=1):
        return 1.0
    if age <= timedelta(days=3):
        return 0.82
    if age <= timedelta(days=7):
        return 0.64
    if age <= timedelta(days=14):
        return 0.42
    return 0.2


def _build_relevance_score(
    *,
    feature: _ItemFeatures,
    tracking_profile: AiHotTrackerTrackingProfile,
) -> float:
    base_score = 0.6 if feature.item.category in set(tracking_profile.enabled_categories) else 0.0
    query_tokens = set(_tokenize(f"{tracking_profile.topic} {tracking_profile.scope}"))
    if not query_tokens:
        return base_score

    item_tokens = set(feature.core_tokens)
    item_tokens.update(token.casefold() for token in feature.item.tags)
    item_tokens.update(token.casefold() for token in feature.item.audience_tags)
    item_tokens.update(_tokenize(feature.item.summary))
    overlap_count = len(query_tokens & item_tokens)
    if overlap_count <= 0:
        return base_score
    bonus = min(0.4, 0.12 * overlap_count)
    return min(1.0, round(base_score + bonus, 4))


def _build_impact_score(*, feature: _ItemFeatures) -> float:
    tokens = set(feature.title_tokens)
    tokens.update(_tokenize(feature.item.summary))
    tokens.update(token.casefold() for token in feature.item.tags)
    tokens.update(token.casefold() for token in feature.item.audience_tags)
    impact = 0.35
    if "ordinary_user" in feature.item.audience_tags:
        impact += 0.16
    if feature.item.category in {"models", "products"}:
        impact += 0.16
    elif feature.item.category in {"developer_tools", "open_source"}:
        impact += 0.10
    elif feature.item.category == "business":
        impact += 0.08
    if feature.item.source_family == "official":
        impact += 0.10
    if feature.item.source_family == "media":
        impact += 0.04
    matched_impact_tokens = len(tokens & _HIGH_IMPACT_TOKENS)
    impact += min(0.22, matched_impact_tokens * 0.055)
    if feature.entity_fingerprint:
        impact += 0.06
    return round(min(1.0, impact), 4)


def _pick_representative_item(items: list[AiHotTrackerSourceItem]) -> AiHotTrackerSourceItem:
    return max(
        items,
        key=lambda item: (
            item.rank_score,
            item.published_at or datetime.min.replace(tzinfo=UTC),
        ),
    )


def _resolve_priority_level(rank_score: float) -> AiHotTrackerPriorityLevel:
    if rank_score >= HIGH_PRIORITY_THRESHOLD:
        return "high"
    if rank_score >= MEDIUM_PRIORITY_THRESHOLD:
        return "medium"
    return "low"


def _build_cluster_snapshot(
    *,
    cluster: AiHotTrackerSignalCluster,
    scored_items_by_id: dict[str, AiHotTrackerSourceItem],
) -> AiHotTrackerClusterSnapshot:
    title_tokens = _tokenize(cluster.title)
    version_tokens = [token for token in title_tokens if _is_version_token(token)]
    return AiHotTrackerClusterSnapshot(
        cluster_id=cluster.cluster_id,
        event_id=cluster.event_id,
        fingerprint=cluster.fingerprint,
        title=cluster.title,
        category=cluster.category,
        representative_item_id=cluster.representative_item_id,
        rank_score=cluster.rank_score,
        priority_level=cluster.priority_level,
        source_item_ids=list(cluster.source_item_ids),
        source_labels=list(cluster.source_labels),
        title_tokens=title_tokens,
        version_tokens=version_tokens,
    )


def _build_rank_reason(
    *,
    novelty_score: float,
    freshness_score: float,
    authority_score: float,
    relevance_score: float,
    impact_score: float,
) -> str:
    reasons: list[str] = []
    if impact_score >= 0.78:
        reasons.append("high user impact")
    elif impact_score >= 0.62:
        reasons.append("clear user impact")

    if novelty_score >= 1.0:
        reasons.append("new signal")
    elif novelty_score >= 0.65:
        reasons.append("updated signal")
    else:
        reasons.append("continuing signal")

    if freshness_score >= 0.82:
        reasons.append("fresh")
    if authority_score >= 0.85:
        reasons.append("high-authority source")
    if relevance_score >= 0.8:
        reasons.append("profile-relevant")
    return ", ".join(reasons)


def _extract_repo_slug(url: str) -> str | None:
    parsed = urlparse(url)
    host = parsed.netloc.casefold()
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if "github.com" not in host or len(parts) < 2:
        return None
    return f"{parts[0].casefold()}/{parts[1].casefold()}"


def _build_canonical_url_stem(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.casefold().removeprefix("www.")
    path_parts = [part.casefold() for part in parsed.path.strip("/").split("/") if part]
    if "github.com" in host and len(path_parts) >= 2:
        return f"{host}/{path_parts[0]}/{path_parts[1]}"
    if not path_parts:
        return host
    return f"{host}/{'/'.join(path_parts[:3])}"


def _extract_entity_fingerprint(tokens: list[str]) -> str | None:
    token_set = set(tokens)
    for entity, aliases in _KNOWN_ENTITIES.items():
        if token_set & aliases:
            return entity
    return None


def _token_overlap_ratio(left: list[str], right: list[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set or not right_set:
        return 0.0
    return len(left_set & right_set) / max(len(left_set), len(right_set))


def _tokenize(value: str) -> list[str]:
    return _WORD_PATTERN.findall(value.casefold())


def _is_version_token(token: str) -> bool:
    return bool(_VERSION_PATTERN.match(token) or _DATE_PATTERN.match(token))


def _unique_in_order(values) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique_values.append(value)
    return unique_values


def _max_priority_level(values) -> AiHotTrackerPriorityLevel:
    resolved: AiHotTrackerPriorityLevel = "low"
    max_weight = -1
    for value in values:
        weight = _PRIORITY_ORDER.get(value, -1)
        if weight > max_weight:
            max_weight = weight
            resolved = value
    return resolved

