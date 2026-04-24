from datetime import UTC, datetime, timedelta

from app.schemas.ai_frontier_research import (
    AiHotTrackerClusterSnapshot,
    AiHotTrackerSignalCluster,
    AiHotTrackerSignalMemoryRecord,
    AiHotTrackerSourceDefinition,
    AiHotTrackerSourceItem,
    AiHotTrackerTrackingProfile,
)
from app.services.ai_hot_tracker_decision_service import (
    build_signal_decision_result,
    build_tracking_delta,
)


def _source_definition(
    *,
    source_id: str,
    label: str,
    category: str,
    authority_weight: float,
    source_family: str = "official",
):
    return AiHotTrackerSourceDefinition(
        id=source_id,
        label=label,
        category=category,
        authority_weight=authority_weight,
        source_family=source_family,
        source_kind="atom_feed",
        feed_url=f"https://example.com/{source_id}.atom",
        tags=[category],
        audience_tags=["ordinary_user"],
    )


def _source_item(
    *,
    item_id: str,
    source_id: str,
    source_label: str,
    category: str,
    title: str,
    url: str,
    published_at: datetime,
    source_family: str = "official",
    tags: list[str] | None = None,
):
    return AiHotTrackerSourceItem(
        id=item_id,
        source_id=source_id,
        source_label=source_label,
        source_kind="atom_feed",
        category=category,
        source_family=source_family,
        title=title,
        url=url,
        summary=title,
        published_at=published_at,
        tags=tags or [category, "agent"],
        audience_tags=["ordinary_user"],
    )


def test_build_signal_decision_result_ranks_user_impact_above_old_authority() -> None:
    now = datetime(2026, 4, 21, 8, 0, tzinfo=UTC)
    profile = AiHotTrackerTrackingProfile()
    source_catalog = [
        _source_definition(
            source_id="vllm-releases",
            label="vLLM Releases",
            category="developer_tools",
            authority_weight=0.86,
            source_family="open_source",
        ),
        _source_definition(
            source_id="openai-news",
            label="OpenAI News",
            category="models",
            authority_weight=0.92,
        ),
    ]
    old_item = _source_item(
        item_id="old-item",
        source_id="vllm-releases",
        source_label="vLLM Releases",
        category="developer_tools",
        source_family="open_source",
        title="vLLM Release v0.8.1",
        url="https://github.com/vllm-project/vllm/releases/tag/v0.8.1",
        published_at=now - timedelta(days=10),
    )
    new_item = _source_item(
        item_id="new-item",
        source_id="openai-news",
        source_label="OpenAI News",
        category="models",
        title="OpenAI launches new ChatGPT agent mode",
        url="https://openai.com/news/chatgpt-agent-mode",
        published_at=now,
        tags=["model", "product", "agent", "chatgpt"],
    )
    previous_snapshot = [
        AiHotTrackerClusterSnapshot(
            cluster_id="cluster-legacy",
            event_id="event-legacy",
            fingerprint="repo:vllm-project/vllm",
            title="vLLM Release v0.8.1",
            category="developer_tools",
            representative_item_id="old-item",
            version_tokens=["v0.8.1"],
        )
    ]

    result = build_signal_decision_result(
        source_catalog=source_catalog,
        source_items=[old_item, new_item],
        tracking_profile=profile,
        previous_snapshot=previous_snapshot,
        reference_time=now,
    )

    assert result.source_items[0].id == "new-item"
    assert result.source_items[0].score_breakdown.impact > result.source_items[1].score_breakdown.impact
    assert result.source_items[0].rank_score > result.source_items[1].rank_score
    assert result.signal_memories
    assert result.signal_memories[0].event_id.startswith("event-")


def test_build_signal_decision_result_clusters_same_repo_releases_conservatively() -> None:
    now = datetime(2026, 4, 21, 8, 0, tzinfo=UTC)
    profile = AiHotTrackerTrackingProfile()
    source_catalog = [
        _source_definition(
            source_id="transformers-releases",
            label="Transformers Releases",
            category="open_source",
            authority_weight=0.82,
            source_family="open_source",
        )
    ]
    result = build_signal_decision_result(
        source_catalog=source_catalog,
        source_items=[
            _source_item(
                item_id="transformers-v4-51",
                source_id="transformers-releases",
                source_label="Transformers Releases",
                category="open_source",
                source_family="open_source",
                title="Transformers Release v4.51.0",
                url="https://github.com/huggingface/transformers/releases/tag/v4.51.0",
                published_at=now,
            ),
            _source_item(
                item_id="transformers-v4-50",
                source_id="transformers-releases",
                source_label="Transformers Releases",
                category="open_source",
                source_family="open_source",
                title="Transformers Release v4.50.0",
                url="https://github.com/huggingface/transformers/releases/tag/v4.50.0",
                published_at=now - timedelta(days=2),
            ),
            _source_item(
                item_id="other-framework",
                source_id="transformers-releases",
                source_label="Transformers Releases",
                category="open_source",
                source_family="open_source",
                title="Different Runtime Adapter",
                url="https://example.com/runtime-adapter",
                published_at=now,
            ),
        ],
        tracking_profile=profile,
        previous_snapshot=None,
        reference_time=now,
    )

    assert len(result.signal_clusters) == 2
    merged_cluster = next(
        cluster for cluster in result.signal_clusters if cluster.title.startswith("Transformers Release")
    )
    assert set(merged_cluster.source_item_ids) == {"transformers-v4-51", "transformers-v4-50"}


def test_build_signal_decision_result_can_merge_official_and_media_same_event() -> None:
    now = datetime(2026, 4, 21, 8, 0, tzinfo=UTC)
    profile = AiHotTrackerTrackingProfile()
    source_catalog = [
        _source_definition(
            source_id="openai-news",
            label="OpenAI News",
            category="models",
            authority_weight=0.92,
        ),
        _source_definition(
            source_id="the-verge-ai",
            label="The Verge AI",
            category="products",
            authority_weight=0.64,
            source_family="media",
        ),
    ]
    result = build_signal_decision_result(
        source_catalog=source_catalog,
        source_items=[
            _source_item(
                item_id="official",
                source_id="openai-news",
                source_label="OpenAI News",
                category="models",
                title="OpenAI launches ChatGPT agent tools",
                url="https://openai.com/news/chatgpt-agent-tools",
                published_at=now,
                tags=["openai", "chatgpt", "agent", "tools"],
            ),
            _source_item(
                item_id="media",
                source_id="the-verge-ai",
                source_label="The Verge AI",
                category="products",
                source_family="media",
                title="OpenAI's ChatGPT agent tools are rolling out",
                url="https://www.theverge.com/ai/openai-chatgpt-agent-tools",
                published_at=now - timedelta(hours=2),
                tags=["openai", "chatgpt", "agent", "tools"],
            ),
        ],
        tracking_profile=profile,
        previous_snapshot=None,
        reference_time=now,
    )

    assert len(result.signal_clusters) == 1
    assert set(result.signal_clusters[0].source_item_ids) == {"official", "media"}


def test_build_tracking_delta_uses_cluster_priority_and_threshold() -> None:
    profile = AiHotTrackerTrackingProfile(alert_threshold=2)
    previous_snapshot = [
        AiHotTrackerClusterSnapshot(
            cluster_id="cluster-existing",
            event_id="event-existing",
            fingerprint="repo:langchain-ai/langchain",
            title="LangChain Release v1.1.0",
            category="developer_tools",
        )
    ]
    current_clusters = [
        AiHotTrackerSignalCluster(
            cluster_id="cluster-existing",
            event_id="event-existing",
            title="LangChain Release v1.1.1",
            category="developer_tools",
            representative_item_id="item-existing",
            source_item_ids=["item-existing"],
            source_labels=["LangChain Releases"],
            rank_score=0.66,
            priority_level="medium",
            fingerprint="repo:langchain-ai/langchain",
            is_new=False,
            is_continuing=True,
            is_cooling=False,
        ),
        AiHotTrackerSignalCluster(
            cluster_id="cluster-new-high",
            event_id="event-new-high",
            title="OpenAI launches new ChatGPT agent mode",
            category="models",
            representative_item_id="item-new",
            source_item_ids=["item-new"],
            source_labels=["OpenAI News"],
            rank_score=0.91,
            priority_level="high",
            fingerprint="entity:openai:agent chatgpt launches mode",
            is_new=True,
            is_continuing=False,
            is_cooling=False,
        ),
    ]

    delta = build_tracking_delta(
        previous_run_id="run-1",
        previous_snapshot=previous_snapshot,
        current_clusters=current_clusters,
        tracking_profile=profile,
        status="completed",
        degraded_reason=None,
    )

    assert delta.change_state == "meaningful_update"
    assert delta.should_notify is True
    assert delta.priority_level == "high"
    assert delta.notify_reason == "发现高优先级新增信号"
    assert delta.new_item_count == 1
    assert delta.continuing_item_count == 1


def test_build_signal_decision_result_increments_signal_memory_streak_for_continuing_signal() -> None:
    now = datetime(2026, 4, 21, 8, 0, tzinfo=UTC)
    profile = AiHotTrackerTrackingProfile()
    source_catalog = [
        _source_definition(
            source_id="openai-news",
            label="OpenAI News",
            category="models",
            authority_weight=0.92,
        )
    ]
    first_result = build_signal_decision_result(
        source_catalog=source_catalog,
        source_items=[
            _source_item(
                item_id="source-old",
                source_id="openai-news",
                source_label="OpenAI News",
                category="models",
                title="OpenAI launches ChatGPT agent tools",
                url="https://openai.com/news/chatgpt-agent-tools",
                published_at=now - timedelta(days=1),
                tags=["openai", "chatgpt", "agent", "tools"],
            )
        ],
        tracking_profile=profile,
        previous_snapshot=None,
        previous_memories=None,
        reference_time=now - timedelta(days=1),
    )

    result = build_signal_decision_result(
        source_catalog=source_catalog,
        source_items=[
            _source_item(
                item_id="source-new",
                source_id="openai-news",
                source_label="OpenAI News",
                category="models",
                title="OpenAI launches ChatGPT agent tools",
                url="https://openai.com/news/chatgpt-agent-tools",
                published_at=now,
                tags=["openai", "chatgpt", "agent", "tools"],
            )
        ],
        tracking_profile=profile,
        previous_snapshot=first_result.cluster_snapshot,
        previous_memories=first_result.signal_memories,
        reference_time=now,
    )

    continuing = next(memory for memory in result.signal_memories if memory.continuity_state == "continuing")
    assert continuing.continuity_state == "continuing"
    assert continuing.activity_state == "continuing"
    assert continuing.streak_count == 2
    assert continuing.cooling_since is None
    assert continuing.superseded_by_event_id is None


def test_build_signal_decision_result_marks_missing_signal_as_replaced_when_newer_event_takes_over() -> None:
    now = datetime(2026, 4, 21, 8, 0, tzinfo=UTC)
    profile = AiHotTrackerTrackingProfile()
    source_catalog = [
        _source_definition(
            source_id="openai-news",
            label="OpenAI News",
            category="models",
            authority_weight=0.92,
        )
    ]
    previous_memories = [
        AiHotTrackerSignalMemoryRecord(
            event_id="event-old-openai-agent-tools",
            fingerprint="entity:openai:agent tools beta",
            title="OpenAI launches ChatGPT agent tools beta",
            category="models",
            first_seen_at=now - timedelta(days=5),
            last_seen_at=now - timedelta(days=1),
            continuity_state="continuing",
            activity_state="continuing",
            source_families=["official"],
            source_item_ids=["source-old"],
            source_labels=["OpenAI News"],
            latest_priority_level="medium",
            latest_rank_score=0.78,
            streak_count=2,
            last_cluster_snapshot={
                "cluster_id": "cluster-old-openai-agent-tools",
                "event_id": "event-old-openai-agent-tools",
                "fingerprint": "entity:openai:agent tools beta",
                "title": "OpenAI launches ChatGPT agent tools beta",
                "category": "models",
                "title_tokens": ["openai", "launches", "chatgpt", "agent", "tools", "beta"],
                "version_tokens": [],
            },
            note="旧信号",
        )
    ]

    result = build_signal_decision_result(
        source_catalog=source_catalog,
        source_items=[
            _source_item(
                item_id="source-new",
                source_id="openai-news",
                source_label="OpenAI News",
                category="models",
                title="OpenAI launches ChatGPT agent mode",
                url="https://openai.com/news/chatgpt-agent-mode",
                published_at=now,
                tags=["openai", "chatgpt", "agent", "mode"],
            )
        ],
        tracking_profile=profile,
        previous_snapshot=None,
        previous_memories=previous_memories,
        reference_time=now,
    )

    replaced = next(
        memory for memory in result.signal_memories if memory.event_id == "event-old-openai-agent-tools"
    )
    assert replaced.continuity_state == "cooling"
    assert replaced.activity_state == "replaced"
    assert replaced.cooling_since == now
    assert replaced.superseded_by_event_id is not None
