from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Literal

from app.schemas.ai_hot_tracker_replay import (
    AiHotTrackerReplayCaseEvaluationResponse,
    AiHotTrackerReplayEvaluationResponse,
    AiHotTrackerReplayStepEvaluationResponse,
)
from app.schemas.ai_frontier_research import (
    AiHotTrackerJudgmentFinding,
    AiHotTrackerSignalMemoryRecord,
    AiHotTrackerSourceDefinition,
    AiHotTrackerSourceItem,
    AiHotTrackerTrackingProfile,
    AiHotTrackerTrackingRunDelta,
)
from app.services.ai_hot_tracker_decision_service import (
    build_signal_decision_result,
    build_tracking_delta,
)

ReplayStatus = Literal["pass", "fail"]


@dataclass(slots=True)
class AiHotTrackerReplayMemoryExpectation:
    title: str
    continuity_state: Literal["new", "continuing", "cooling"] | None = None
    activity_state: Literal["heating", "continuing", "cooling", "replaced"] | None = None
    streak_count: int | None = None
    has_superseded_by_event_id: bool | None = None


@dataclass(slots=True)
class AiHotTrackerReplayStepExpectation:
    top_ranked_item_id: str | None = None
    cluster_count: int | None = None
    delta_change_state: str | None = None
    should_notify: bool | None = None
    notify_reason: str | None = None
    merged_source_item_groups: list[tuple[str, ...]] = field(default_factory=list)
    memory_expectations: list[AiHotTrackerReplayMemoryExpectation] = field(default_factory=list)


@dataclass(slots=True)
class AiHotTrackerReplayStepSpec:
    label: str
    items: list[AiHotTrackerSourceItem]
    expectation: AiHotTrackerReplayStepExpectation


@dataclass(slots=True)
class AiHotTrackerReplayCaseSpec:
    case_id: str
    title: str
    description: str
    source_catalog: list[AiHotTrackerSourceDefinition]
    tracking_profile: AiHotTrackerTrackingProfile
    reference_time: datetime
    steps: list[AiHotTrackerReplayStepSpec]


@dataclass(slots=True)
class AiHotTrackerReplayStepResult:
    label: str
    delta: AiHotTrackerTrackingRunDelta
    ranked_item_ids: list[str]
    cluster_titles: list[str]
    event_memories: list[AiHotTrackerSignalMemoryRecord]
    findings: list[AiHotTrackerJudgmentFinding]

    @property
    def status(self) -> ReplayStatus:
        return "fail" if any(finding.status == "fail" for finding in self.findings) else "pass"


@dataclass(slots=True)
class AiHotTrackerReplayCaseResult:
    case_id: str
    title: str
    description: str
    steps: list[AiHotTrackerReplayStepResult]

    @property
    def status(self) -> ReplayStatus:
        return "fail" if any(step.status == "fail" for step in self.steps) else "pass"


@dataclass(slots=True)
class AiHotTrackerReplaySuiteResult:
    cases: list[AiHotTrackerReplayCaseResult]

    @property
    def total_case_count(self) -> int:
        return len(self.cases)

    @property
    def failed_case_count(self) -> int:
        return sum(1 for case in self.cases if case.status == "fail")

    @property
    def passed_case_count(self) -> int:
        return self.total_case_count - self.failed_case_count

    @property
    def status(self) -> ReplayStatus:
        return "fail" if self.failed_case_count else "pass"


def _source_definition(
    *,
    source_id: str,
    label: str,
    category: str,
    authority_weight: float,
    source_family: Literal["official", "media", "research", "open_source"],
    tags: list[str],
    audience_tags: list[str],
) -> AiHotTrackerSourceDefinition:
    return AiHotTrackerSourceDefinition(
        id=source_id,
        label=label,
        category=category,
        source_family=source_family,
        source_kind="atom_feed",
        feed_url=f"https://example.com/{source_id}.xml",
        tags=tags,
        audience_tags=audience_tags,
        authority_weight=authority_weight,
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
    summary: str,
    source_family: Literal["official", "media", "research", "open_source"],
    tags: list[str],
    audience_tags: list[str],
) -> AiHotTrackerSourceItem:
    return AiHotTrackerSourceItem(
        id=item_id,
        source_id=source_id,
        source_label=source_label,
        source_kind="html_list" if source_family in {"official", "media"} else "rss_feed",
        category=category,
        source_family=source_family,
        title=title,
        url=url,
        summary=summary,
        published_at=published_at,
        tags=tags,
        audience_tags=audience_tags,
    )


def _finding(
    *,
    code: str,
    passed: bool,
    passed_summary: str,
    failed_summary: str,
    details: dict[str, object],
) -> AiHotTrackerJudgmentFinding:
    return AiHotTrackerJudgmentFinding(
        code=code,
        status="pass" if passed else "fail",
        summary=passed_summary if passed else failed_summary,
        details=details,
    )


def _evaluate_step(
    *,
    expectation: AiHotTrackerReplayStepExpectation,
    ranked_item_ids: list[str],
    clusters: list[tuple[str, list[str]]],
    delta: AiHotTrackerTrackingRunDelta,
    event_memories: list[AiHotTrackerSignalMemoryRecord],
) -> list[AiHotTrackerJudgmentFinding]:
    findings: list[AiHotTrackerJudgmentFinding] = []

    if expectation.top_ranked_item_id is not None:
        actual_top = ranked_item_ids[0] if ranked_item_ids else None
        findings.append(
            _finding(
                code="top_ranked_item",
                passed=actual_top == expectation.top_ranked_item_id,
                passed_summary="最高优先信号符合 replay 预期。",
                failed_summary="最高优先信号与 replay 预期不一致。",
                details={
                    "expected": expectation.top_ranked_item_id,
                    "actual": actual_top,
                    "ranked_item_ids": ranked_item_ids,
                },
            )
        )

    if expectation.cluster_count is not None:
        findings.append(
            _finding(
                code="cluster_count",
                passed=len(clusters) == expectation.cluster_count,
                passed_summary="聚类数量符合 replay 预期。",
                failed_summary="聚类数量与 replay 预期不一致。",
                details={
                    "expected": expectation.cluster_count,
                    "actual": len(clusters),
                    "clusters": [{"title": title, "source_item_ids": item_ids} for title, item_ids in clusters],
                },
            )
        )

    if expectation.delta_change_state is not None:
        findings.append(
            _finding(
                code="delta_change_state",
                passed=delta.change_state == expectation.delta_change_state,
                passed_summary="变化状态符合 replay 预期。",
                failed_summary="变化状态与 replay 预期不一致。",
                details={
                    "expected": expectation.delta_change_state,
                    "actual": delta.change_state,
                    "delta": delta.model_dump(mode="json"),
                },
            )
        )

    if expectation.should_notify is not None:
        findings.append(
            _finding(
                code="delta_should_notify",
                passed=delta.should_notify is expectation.should_notify,
                passed_summary="提醒判断符合 replay 预期。",
                failed_summary="提醒判断与 replay 预期不一致。",
                details={
                    "expected": expectation.should_notify,
                    "actual": delta.should_notify,
                    "notify_reason": delta.notify_reason,
                },
            )
        )

    if expectation.notify_reason is not None:
        findings.append(
            _finding(
                code="delta_notify_reason",
                passed=delta.notify_reason == expectation.notify_reason,
                passed_summary="提醒原因符合 replay 预期。",
                failed_summary="提醒原因与 replay 预期不一致。",
                details={
                    "expected": expectation.notify_reason,
                    "actual": delta.notify_reason,
                },
            )
        )

    for expected_group in expectation.merged_source_item_groups:
        expected_set = set(expected_group)
        matched_cluster = next(
            (
                {"title": title, "source_item_ids": item_ids}
                for title, item_ids in clusters
                if expected_set.issubset(set(item_ids))
            ),
            None,
        )
        findings.append(
            _finding(
                code=f"merged_group_{'-'.join(expected_group)}",
                passed=matched_cluster is not None,
                passed_summary="同一事件来源被保守合并到同一信号。",
                failed_summary="同一事件来源没有按预期合并到同一信号。",
                details={
                    "expected_group": list(expected_group),
                    "matched_cluster": matched_cluster,
                },
            )
        )

    memory_by_title = {memory.title: memory for memory in event_memories}
    for memory_expectation in expectation.memory_expectations:
        memory = memory_by_title.get(memory_expectation.title)
        findings.append(
            _finding(
                code=f"memory_presence_{memory_expectation.title}",
                passed=memory is not None,
                passed_summary="事件记忆存在。",
                failed_summary="事件记忆缺失。",
                details={"title": memory_expectation.title},
            )
        )
        if memory is None:
            continue

        if memory_expectation.continuity_state is not None:
            findings.append(
                _finding(
                    code=f"memory_continuity_{memory_expectation.title}",
                    passed=memory.continuity_state == memory_expectation.continuity_state,
                    passed_summary="事件记忆连续性符合预期。",
                    failed_summary="事件记忆连续性与预期不一致。",
                    details={
                        "title": memory_expectation.title,
                        "expected": memory_expectation.continuity_state,
                        "actual": memory.continuity_state,
                    },
                )
            )

        if memory_expectation.activity_state is not None:
            findings.append(
                _finding(
                    code=f"memory_activity_{memory_expectation.title}",
                    passed=memory.activity_state == memory_expectation.activity_state,
                    passed_summary="事件记忆活动状态符合预期。",
                    failed_summary="事件记忆活动状态与预期不一致。",
                    details={
                        "title": memory_expectation.title,
                        "expected": memory_expectation.activity_state,
                        "actual": memory.activity_state,
                    },
                )
            )

        if memory_expectation.streak_count is not None:
            findings.append(
                _finding(
                    code=f"memory_streak_{memory_expectation.title}",
                    passed=memory.streak_count == memory_expectation.streak_count,
                    passed_summary="事件记忆 streak 符合预期。",
                    failed_summary="事件记忆 streak 与预期不一致。",
                    details={
                        "title": memory_expectation.title,
                        "expected": memory_expectation.streak_count,
                        "actual": memory.streak_count,
                    },
                )
            )

        if memory_expectation.has_superseded_by_event_id is not None:
            has_superseded = bool(memory.superseded_by_event_id)
            findings.append(
                _finding(
                    code=f"memory_superseded_{memory_expectation.title}",
                    passed=has_superseded is memory_expectation.has_superseded_by_event_id,
                    passed_summary="事件替代关系符合预期。",
                    failed_summary="事件替代关系与预期不一致。",
                    details={
                        "title": memory_expectation.title,
                        "expected": memory_expectation.has_superseded_by_event_id,
                        "actual": has_superseded,
                        "superseded_by_event_id": memory.superseded_by_event_id,
                    },
                )
            )

    return findings


def _build_replay_cases() -> list[AiHotTrackerReplayCaseSpec]:
    now = datetime(2026, 4, 24, 10, 0, tzinfo=UTC)
    default_profile = AiHotTrackerTrackingProfile()
    research_threshold_profile = AiHotTrackerTrackingProfile(
        alert_threshold=2,
        enabled_categories=["research"],
    )

    official_vs_open_source_catalog = [
        _source_definition(
            source_id="openai-news",
            label="OpenAI News",
            category="models",
            authority_weight=0.92,
            source_family="official",
            tags=["model", "product", "agent", "chatgpt"],
            audience_tags=["ordinary_user", "product_builder"],
        ),
        _source_definition(
            source_id="vllm-releases",
            label="vLLM Releases",
            category="developer_tools",
            authority_weight=0.86,
            source_family="open_source",
            tags=["release", "inference"],
            audience_tags=["developer"],
        ),
    ]

    merge_catalog = [
        _source_definition(
            source_id="openai-news",
            label="OpenAI News",
            category="models",
            authority_weight=0.92,
            source_family="official",
            tags=["model", "product", "agent", "chatgpt"],
            audience_tags=["ordinary_user", "product_builder"],
        ),
        _source_definition(
            source_id="the-verge-ai",
            label="The Verge AI",
            category="products",
            authority_weight=0.64,
            source_family="media",
            tags=["media", "product", "agent", "chatgpt"],
            audience_tags=["ordinary_user"],
        ),
    ]

    research_catalog = [
        _source_definition(
            source_id="arxiv-cs-ai",
            label="arXiv cs.AI",
            category="research",
            authority_weight=0.78,
            source_family="research",
            tags=["paper", "agent"],
            audience_tags=["learner", "developer"],
        )
    ]

    return [
        AiHotTrackerReplayCaseSpec(
            case_id="official-impact-beats-old-open-source",
            title="官方高影响更新应压过老旧开源 release",
            description="新鲜且高影响的官方产品信号不应被老旧的高权重开源更新压住。",
            source_catalog=official_vs_open_source_catalog,
            tracking_profile=default_profile,
            reference_time=now,
            steps=[
                AiHotTrackerReplayStepSpec(
                    label="first-run",
                    items=[
                        _source_item(
                            item_id="old-vllm-release",
                            source_id="vllm-releases",
                            source_label="vLLM Releases",
                            category="developer_tools",
                            title="vLLM Release v0.8.1",
                            url="https://github.com/vllm-project/vllm/releases/tag/v0.8.1",
                            published_at=now - timedelta(days=10),
                            summary="One older open-source inference runtime release.",
                            source_family="open_source",
                            tags=["release", "inference"],
                            audience_tags=["developer"],
                        ),
                        _source_item(
                            item_id="official-agent-mode",
                            source_id="openai-news",
                            source_label="OpenAI News",
                            category="models",
                            title="OpenAI launches ChatGPT agent mode",
                            url="https://openai.com/news/chatgpt-agent-mode",
                            published_at=now,
                            summary="ChatGPT moves closer to task execution for ordinary users.",
                            source_family="official",
                            tags=["chatgpt", "agent", "product", "model"],
                            audience_tags=["ordinary_user", "product_builder"],
                        ),
                    ],
                    expectation=AiHotTrackerReplayStepExpectation(
                        top_ranked_item_id="official-agent-mode",
                        cluster_count=2,
                        delta_change_state="first_run",
                        should_notify=True,
                        memory_expectations=[
                            AiHotTrackerReplayMemoryExpectation(
                                title="OpenAI launches ChatGPT agent mode",
                                continuity_state="new",
                                activity_state="heating",
                                streak_count=1,
                                has_superseded_by_event_id=False,
                            )
                        ],
                    ),
                )
            ],
        ),
        AiHotTrackerReplayCaseSpec(
            case_id="official-and-media-merge-same-event",
            title="官方发布与媒体跟进应保守合并为同一事件",
            description="同一事件的官方说明和精选媒体跟进不应拆成两个完全独立的主信号。",
            source_catalog=merge_catalog,
            tracking_profile=default_profile,
            reference_time=now,
            steps=[
                AiHotTrackerReplayStepSpec(
                    label="same-event-merge",
                    items=[
                        _source_item(
                            item_id="official-launch",
                            source_id="openai-news",
                            source_label="OpenAI News",
                            category="models",
                            title="OpenAI launches ChatGPT agent tools",
                            url="https://openai.com/news/chatgpt-agent-tools",
                            published_at=now,
                            summary="Official launch for ChatGPT agent tools.",
                            source_family="official",
                            tags=["openai", "chatgpt", "agent", "tools"],
                            audience_tags=["ordinary_user", "product_builder"],
                        ),
                        _source_item(
                            item_id="media-rollout",
                            source_id="the-verge-ai",
                            source_label="The Verge AI",
                            category="products",
                            title="OpenAI's ChatGPT agent tools are rolling out",
                            url="https://www.theverge.com/ai/openai-chatgpt-agent-tools",
                            published_at=now - timedelta(hours=2),
                            summary="Media coverage for the same ChatGPT agent tools rollout.",
                            source_family="media",
                            tags=["openai", "chatgpt", "agent", "tools"],
                            audience_tags=["ordinary_user"],
                        ),
                    ],
                    expectation=AiHotTrackerReplayStepExpectation(
                        cluster_count=1,
                        delta_change_state="first_run",
                        should_notify=True,
                        merged_source_item_groups=[("official-launch", "media-rollout")],
                    ),
                )
            ],
        ),
        AiHotTrackerReplayCaseSpec(
            case_id="steady-state-repeated-signal-keeps-streak",
            title="重复出现的同一信号应进入 steady state 并累积 streak",
            description="第二轮同信号重复出现时，不应继续触发重要变化提醒，但要保留连续记忆。",
            source_catalog=merge_catalog[:1],
            tracking_profile=default_profile,
            reference_time=now,
            steps=[
                AiHotTrackerReplayStepSpec(
                    label="first-run",
                    items=[
                        _source_item(
                            item_id="agent-tools-day-1",
                            source_id="openai-news",
                            source_label="OpenAI News",
                            category="models",
                            title="OpenAI launches ChatGPT agent tools",
                            url="https://openai.com/news/chatgpt-agent-tools",
                            published_at=now - timedelta(days=1),
                            summary="Initial launch of ChatGPT agent tools.",
                            source_family="official",
                            tags=["openai", "chatgpt", "agent", "tools"],
                            audience_tags=["ordinary_user", "product_builder"],
                        )
                    ],
                    expectation=AiHotTrackerReplayStepExpectation(
                        delta_change_state="first_run",
                        should_notify=True,
                    ),
                ),
                AiHotTrackerReplayStepSpec(
                    label="repeated-run",
                    items=[
                        _source_item(
                            item_id="agent-tools-day-2",
                            source_id="openai-news",
                            source_label="OpenAI News",
                            category="models",
                            title="OpenAI launches ChatGPT agent tools",
                            url="https://openai.com/news/chatgpt-agent-tools",
                            published_at=now,
                            summary="The same signal remains visible on the next run.",
                            source_family="official",
                            tags=["openai", "chatgpt", "agent", "tools"],
                            audience_tags=["ordinary_user", "product_builder"],
                        )
                    ],
                    expectation=AiHotTrackerReplayStepExpectation(
                        delta_change_state="steady_state",
                        should_notify=False,
                        memory_expectations=[
                            AiHotTrackerReplayMemoryExpectation(
                                title="OpenAI launches ChatGPT agent tools",
                                continuity_state="continuing",
                                activity_state="continuing",
                                streak_count=2,
                                has_superseded_by_event_id=False,
                            )
                        ],
                    ),
                ),
            ],
        ),
        AiHotTrackerReplayCaseSpec(
            case_id="threshold-driven-meaningful-update",
            title="达到阈值的两个中高优先级新信号应触发提醒",
            description="meaningful update 不应只看单个高优先级信号，也要支持阈值驱动。",
            source_catalog=research_catalog,
            tracking_profile=research_threshold_profile,
            reference_time=now,
            steps=[
                AiHotTrackerReplayStepSpec(
                    label="baseline-run",
                    items=[
                        _source_item(
                            item_id="paper-existing",
                            source_id="arxiv-cs-ai",
                            source_label="arXiv cs.AI",
                            category="research",
                            title="Agent coordination paper",
                            url="https://arxiv.org/abs/2604.00001",
                            published_at=now - timedelta(days=2),
                            summary="A continuing research signal around coordination.",
                            source_family="research",
                            tags=["paper", "agent"],
                            audience_tags=["learner", "developer"],
                        )
                    ],
                    expectation=AiHotTrackerReplayStepExpectation(
                        delta_change_state="first_run",
                        should_notify=True,
                    ),
                ),
                AiHotTrackerReplayStepSpec(
                    label="threshold-run",
                    items=[
                        _source_item(
                            item_id="paper-existing-2",
                            source_id="arxiv-cs-ai",
                            source_label="arXiv cs.AI",
                            category="research",
                            title="Agent coordination paper",
                            url="https://arxiv.org/abs/2604.00001",
                            published_at=now,
                            summary="The same coordination signal continues.",
                            source_family="research",
                            tags=["paper", "agent"],
                            audience_tags=["learner", "developer"],
                        ),
                        _source_item(
                            item_id="paper-memory",
                            source_id="arxiv-cs-ai",
                            source_label="arXiv cs.AI",
                            category="research",
                            title="Agent memory paper",
                            url="https://arxiv.org/abs/2604.00002",
                            published_at=now,
                            summary="A new paper focused on agent memory systems.",
                            source_family="research",
                            tags=["paper", "agent", "memory"],
                            audience_tags=["learner", "developer"],
                        ),
                        _source_item(
                            item_id="paper-evals",
                            source_id="arxiv-cs-ai",
                            source_label="arXiv cs.AI",
                            category="research",
                            title="Agent evals paper",
                            url="https://arxiv.org/abs/2604.00003",
                            published_at=now,
                            summary="A new paper focused on evaluating agent systems.",
                            source_family="research",
                            tags=["paper", "agent", "benchmark"],
                            audience_tags=["learner", "developer"],
                        ),
                    ],
                    expectation=AiHotTrackerReplayStepExpectation(
                        delta_change_state="meaningful_update",
                        should_notify=True,
                        notify_reason="新增中高优先级信号达到阈值 2",
                    ),
                ),
            ],
        ),
        AiHotTrackerReplayCaseSpec(
            case_id="replacement-signal-creates-superseded-memory",
            title="新事件替代旧事件时应显式标记 superseded",
            description="热点不只是出现或消失，还需要表达旧信号被新信号替代。",
            source_catalog=merge_catalog[:1],
            tracking_profile=default_profile,
            reference_time=now,
            steps=[
                AiHotTrackerReplayStepSpec(
                    label="beta-run",
                    items=[
                        _source_item(
                            item_id="beta-signal",
                            source_id="openai-news",
                            source_label="OpenAI News",
                            category="models",
                            title="OpenAI launches ChatGPT agent tools beta",
                            url="https://openai.com/news/chatgpt-agent-tools-beta",
                            published_at=now - timedelta(days=2),
                            summary="Early beta signal for ChatGPT agent tools.",
                            source_family="official",
                            tags=["openai", "chatgpt", "agent", "tools"],
                            audience_tags=["ordinary_user", "product_builder"],
                        )
                    ],
                    expectation=AiHotTrackerReplayStepExpectation(
                        delta_change_state="first_run",
                        should_notify=True,
                    ),
                ),
                AiHotTrackerReplayStepSpec(
                    label="mode-run",
                    items=[
                        _source_item(
                            item_id="agent-mode",
                            source_id="openai-news",
                            source_label="OpenAI News",
                            category="models",
                            title="OpenAI launches ChatGPT agent mode",
                            url="https://openai.com/news/chatgpt-agent-mode",
                            published_at=now,
                            summary="A newer and stronger signal that supersedes the older beta framing.",
                            source_family="official",
                            tags=["openai", "chatgpt", "agent", "mode"],
                            audience_tags=["ordinary_user", "product_builder"],
                        )
                    ],
                    expectation=AiHotTrackerReplayStepExpectation(
                        delta_change_state="meaningful_update",
                        should_notify=True,
                        notify_reason="发现高优先级新增信号",
                        memory_expectations=[
                            AiHotTrackerReplayMemoryExpectation(
                                title="OpenAI launches ChatGPT agent tools beta",
                                continuity_state="cooling",
                                activity_state="replaced",
                                streak_count=1,
                                has_superseded_by_event_id=True,
                            ),
                            AiHotTrackerReplayMemoryExpectation(
                                title="OpenAI launches ChatGPT agent mode",
                                continuity_state="new",
                                activity_state="heating",
                                streak_count=1,
                                has_superseded_by_event_id=False,
                            ),
                        ],
                    ),
                ),
            ],
        ),
    ]


def run_ai_hot_tracker_replay_suite() -> AiHotTrackerReplaySuiteResult:
    case_results: list[AiHotTrackerReplayCaseResult] = []

    for case in _build_replay_cases():
        previous_snapshot = None
        previous_memories: list[AiHotTrackerSignalMemoryRecord] | None = None
        previous_run_id: str | None = None
        step_results: list[AiHotTrackerReplayStepResult] = []

        for step_index, step in enumerate(case.steps):
            evaluated_at = case.reference_time + timedelta(minutes=step_index)
            decision_result = build_signal_decision_result(
                source_catalog=case.source_catalog,
                source_items=step.items,
                tracking_profile=case.tracking_profile,
                previous_snapshot=previous_snapshot,
                previous_memories=previous_memories,
                reference_time=evaluated_at,
            )
            delta = build_tracking_delta(
                previous_run_id=previous_run_id,
                previous_snapshot=previous_snapshot,
                current_clusters=decision_result.signal_clusters,
                tracking_profile=case.tracking_profile,
                status="completed",
                degraded_reason=None,
            )
            ranked_item_ids = [item.id for item in decision_result.source_items]
            clusters = [
                (cluster.title, list(cluster.source_item_ids))
                for cluster in decision_result.signal_clusters
            ]
            findings = _evaluate_step(
                expectation=step.expectation,
                ranked_item_ids=ranked_item_ids,
                clusters=clusters,
                delta=delta,
                event_memories=decision_result.signal_memories,
            )
            step_results.append(
                AiHotTrackerReplayStepResult(
                    label=step.label,
                    delta=delta,
                    ranked_item_ids=ranked_item_ids,
                    cluster_titles=[cluster.title for cluster in decision_result.signal_clusters],
                    event_memories=decision_result.signal_memories,
                    findings=findings,
                )
            )
            previous_snapshot = decision_result.cluster_snapshot
            previous_memories = decision_result.signal_memories
            previous_run_id = f"replay-{case.case_id}-{step_index + 1}"

        case_results.append(
            AiHotTrackerReplayCaseResult(
                case_id=case.case_id,
                title=case.title,
                description=case.description,
                steps=step_results,
            )
        )

    return AiHotTrackerReplaySuiteResult(cases=case_results)


def get_ai_hot_tracker_replay_evaluation() -> AiHotTrackerReplayEvaluationResponse:
    suite = run_ai_hot_tracker_replay_suite()
    return AiHotTrackerReplayEvaluationResponse(
        status=suite.status,
        total_case_count=suite.total_case_count,
        passed_case_count=suite.passed_case_count,
        failed_case_count=suite.failed_case_count,
        cases=[
            AiHotTrackerReplayCaseEvaluationResponse(
                case_id=case.case_id,
                title=case.title,
                description=case.description,
                status=case.status,
                steps=[
                    AiHotTrackerReplayStepEvaluationResponse(
                        label=step.label,
                        status=step.status,
                        delta_change_state=step.delta.change_state,
                        should_notify=step.delta.should_notify,
                        notify_reason=step.delta.notify_reason,
                        ranked_item_ids=step.ranked_item_ids,
                        cluster_titles=step.cluster_titles,
                        findings=step.findings,
                    )
                    for step in case.steps
                ],
            )
            for case in suite.cases
        ],
    )
