from datetime import UTC, datetime

from pytest import MonkeyPatch

from app.schemas.ai_frontier_research import (
    AiHotTrackerSourceDefinition,
    AiHotTrackerSourceFailure,
    AiHotTrackerSourceItem,
)
from app.services import ai_hot_tracker_report_service
from app.services.ai_hot_tracker_report_service import generate_ai_hot_tracker_report
from app.services.ai_hot_tracker_source_service import _parse_html_list, _parse_source_feed
from app.services.model_interface_service import ModelInterfaceError


class FakeJsonModelInterface:
    def __init__(self, responses: list[dict[str, object]] | dict[str, object]) -> None:
        self._responses = [responses] if isinstance(responses, dict) else responses
        self.calls: list[dict[str, object]] = []

    def generate_json_object(self, **kwargs):
        self.calls.append(kwargs)
        from app.services.model_interface_service import ModelJsonResponse, ModelUsage

        if not self._responses:
            raise AssertionError("No more fake responses configured")

        return ModelJsonResponse(
            data=self._responses.pop(0),
            text="{}",
            usage=ModelUsage(input_tokens=12, output_tokens=18, total_tokens=30),
        )


class FailingJsonModelInterface:
    def generate_json_object(self, **kwargs):
        raise ModelInterfaceError("model unavailable")


def _mock_workspace(*_, **__):
    return type("Workspace", (), {"module_type": "research", "module_config_json": {}})()


def _sample_items(generated_at: datetime) -> list[AiHotTrackerSourceItem]:
    return [
        AiHotTrackerSourceItem(
            id="source-1",
            source_id="openai-news",
            source_label="OpenAI News",
            source_kind="html_list",
            category="models",
            source_family="official",
            title="OpenAI launches ChatGPT agent tools",
            url="https://openai.com/news/chatgpt-agent-tools",
            summary="OpenAI introduces agent tools for ChatGPT users.",
            published_at=generated_at,
            tags=["model", "product", "agent", "chatgpt"],
            audience_tags=["ordinary_user", "product_builder"],
        ),
        AiHotTrackerSourceItem(
            id="source-2",
            source_id="arxiv-cs-ai",
            source_label="arXiv cs.AI",
            source_kind="rss_feed",
            category="research",
            source_family="research",
            title="New Agent Training Paper",
            url="https://arxiv.org/abs/2604.00001",
            summary="Shows stronger coordination behavior.",
            published_at=generated_at,
            tags=["paper", "agent"],
            audience_tags=["learner", "developer"],
        ),
    ]


def _mock_intake(monkeypatch: MonkeyPatch, intake_items: list[AiHotTrackerSourceItem]) -> None:
    monkeypatch.setattr(ai_hot_tracker_report_service.workspace_repository, "get_workspace", _mock_workspace)
    monkeypatch.setattr(
        ai_hot_tracker_report_service,
        "fetch_ai_hot_tracker_source_items",
        lambda total_limit=24: ai_hot_tracker_report_service.AiHotTrackerSourceIntakeResult(
            source_catalog=[
                AiHotTrackerSourceDefinition(
                    id="openai-news",
                    label="OpenAI News",
                    category="models",
                    source_family="official",
                    source_kind="html_list",
                    feed_url="https://openai.com/news/",
                    tags=["model", "product"],
                    audience_tags=["ordinary_user"],
                    authority_weight=0.92,
                ),
                AiHotTrackerSourceDefinition(
                    id="arxiv-cs-ai",
                    label="arXiv cs.AI",
                    category="research",
                    source_family="research",
                    source_kind="rss_feed",
                    feed_url="https://example.com/papers.rss",
                    tags=["paper"],
                    audience_tags=["learner"],
                    authority_weight=0.78,
                ),
            ],
            source_items=intake_items,
            source_failures=[
                AiHotTrackerSourceFailure(
                    source_id="arxiv-cs-ai",
                    source_label="arXiv cs.AI",
                    message="timeout",
                )
            ],
        ),
    )


def _valid_brief_payload() -> dict[str, object]:
    return {
        "headline": "ChatGPT agent tools are the clearest signal this round",
        "summary": "This round is most useful for users watching how AI products become action tools.",
        "change_state": "meaningful_update",
        "signals": [
            {
                "title": "ChatGPT agent tools move from concept to product",
                "summary": "OpenAI is positioning ChatGPT around more direct task execution.",
                "why_now": "It changes what mainstream users can expect from AI assistants.",
                "impact": "普通用户会更早遇到能执行任务的 AI 产品，而不只是问答工具。",
                "audience": ["AI 用户", "产品人"],
                "change_type": "new",
                "priority_level": "high",
                "confidence": "high",
                "source_item_ids": ["source-1"],
            }
        ],
        "keep_watching": [
            {
                "title": "Agent training research",
                "reason": "The research signal is strengthening but still needs more product evidence.",
                "source_item_ids": ["source-2"],
            }
        ],
        "blindspots": ["还需要继续确认这些 agent 能力会不会稳定进入真实产品。"],
    }


def test_generate_ai_hot_tracker_report_builds_structured_output(monkeypatch: MonkeyPatch) -> None:
    generated_at = datetime(2026, 4, 16, 8, 0, tzinfo=UTC)
    intake_items = _sample_items(generated_at)
    _mock_intake(monkeypatch, intake_items)
    fake_interface = FakeJsonModelInterface(_valid_brief_payload())
    monkeypatch.setattr(ai_hot_tracker_report_service, "get_chat_model_interface", lambda: fake_interface)

    result = generate_ai_hot_tracker_report(workspace_id="workspace-1", user_id="user-1")

    assert result.title == "ChatGPT agent tools are the clearest signal this round"
    assert result.output.headline == result.title
    assert result.output.signals[0].impact.startswith("普通用户")
    assert result.output.signals[0].audience == ["AI 用户", "产品人"]
    assert result.output.signals[0].confidence == "high"
    assert result.output.blindspots == ["还需要继续确认这些 agent 能力会不会稳定进入真实产品。"]
    assert result.output.reference_sources[0].url == "https://openai.com/news/chatgpt-agent-tools"
    assert result.output.reference_sources[1].source_kind == "paper"
    assert result.degraded_reason is None
    assert result.source_set["mode"] == "ai_hot_tracker_tracking_agent"
    assert len(result.source_set["signal_clusters"]) >= 1
    assert len(result.source_set["event_memories"]) >= 1
    assert any(trace["role"] == "scout" for trace in result.source_set["agent_trace"])
    assert len(fake_interface.calls) == 1


def test_generate_ai_hot_tracker_report_repairs_invalid_first_draft(monkeypatch: MonkeyPatch) -> None:
    generated_at = datetime(2026, 4, 16, 8, 0, tzinfo=UTC)
    intake_items = _sample_items(generated_at)
    _mock_intake(monkeypatch, intake_items)
    fake_interface = FakeJsonModelInterface(
        [
            {
                "headline": "Broken draft",
                "summary": "Missing required fields in signals.",
                "change_state": "meaningful_update",
                "signals": [{"title": "Broken signal"}],
                "keep_watching": [],
            },
            _valid_brief_payload(),
        ]
    )
    monkeypatch.setattr(ai_hot_tracker_report_service, "get_chat_model_interface", lambda: fake_interface)

    result = generate_ai_hot_tracker_report(workspace_id="workspace-1", user_id="user-1")

    assert result.output.signals
    assert result.output.blindspots
    assert result.output.reference_sources[0].url == "https://openai.com/news/chatgpt-agent-tools"
    assert len(fake_interface.calls) == 2


def test_generate_ai_hot_tracker_report_returns_degraded_response_when_model_generation_fails(
    monkeypatch: MonkeyPatch,
) -> None:
    generated_at = datetime(2026, 4, 16, 8, 0, tzinfo=UTC)
    intake_items = _sample_items(generated_at)
    _mock_intake(monkeypatch, intake_items)
    monkeypatch.setattr(ai_hot_tracker_report_service, "get_chat_model_interface", lambda: FailingJsonModelInterface())

    result = generate_ai_hot_tracker_report(workspace_id="workspace-1", user_id="user-1")

    assert result.degraded_reason == "report_generation_failed"
    assert result.output.change_state == "degraded"
    assert result.title == "本轮简报暂未生成"
    assert result.output.summary == "来源已经更新，但结构化简报还没有成功生成。这一轮暂时不作为正式判断使用。"
    assert result.output.blindspots


def test_generate_ai_hot_tracker_report_returns_degraded_response_when_no_items(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(ai_hot_tracker_report_service.workspace_repository, "get_workspace", _mock_workspace)
    monkeypatch.setattr(
        ai_hot_tracker_report_service,
        "fetch_ai_hot_tracker_source_items",
        lambda total_limit=24: ai_hot_tracker_report_service.AiHotTrackerSourceIntakeResult(
            source_catalog=[],
            source_items=[],
            source_failures=[],
        ),
    )

    result = generate_ai_hot_tracker_report(workspace_id="workspace-1", user_id="user-1")

    assert result.degraded_reason == "source_intake_unavailable"
    assert result.output.change_state == "degraded"
    assert result.title == "本轮暂时没有可用热点"
    assert result.output.summary == "这次没有拿到足够有效的来源，因此还不能形成可信的热点判断。"
    assert result.output.blindspots == ["这一轮缺少足够稳定的候选信号，仍需等待更完整来源。"]


def test_source_parsers_support_media_rss_and_official_html() -> None:
    rss_source = AiHotTrackerSourceDefinition(
        id="media-feed",
        label="Media Feed",
        category="business",
        source_family="media",
        source_kind="rss_feed",
        feed_url="https://example.com/feed.xml",
        tags=["media"],
        audience_tags=["ordinary_user"],
    )
    rss_items = _parse_source_feed(
        source=rss_source,
        payload="""
        <rss><channel><item>
          <title>AI product funding changes the market</title>
          <link>https://example.com/ai-product-funding</link>
          <description>Funding pressure changes product competition.</description>
          <pubDate>Tue, 21 Apr 2026 08:00:00 GMT</pubDate>
        </item></channel></rss>
        """,
    )

    html_source = AiHotTrackerSourceDefinition(
        id="official-html",
        label="Official HTML",
        category="models",
        source_family="official",
        source_kind="html_list",
        feed_url="https://example.com/news/",
        tags=["model"],
        audience_tags=["ordinary_user"],
    )
    html_items = _parse_html_list(
        source=html_source,
        payload="""
        <article>
          <a href="/news/model-launch">New model launch changes AI product use</a>
          <time datetime="2026-04-21T08:00:00Z"></time>
          <p>A new model release reaches mainstream product users.</p>
        </article>
        """,
    )

    assert rss_items[0].source_family == "media"
    assert rss_items[0].summary == "Funding pressure changes product competition."
    assert html_items[0].source_family == "official"
    assert html_items[0].url == "https://example.com/news/model-launch"
