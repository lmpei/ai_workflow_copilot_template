from datetime import UTC, datetime

from pytest import MonkeyPatch

from app.schemas.ai_frontier_research import (
    AiHotTrackerSourceDefinition,
    AiHotTrackerSourceFailure,
    AiHotTrackerSourceItem,
)
from app.services import ai_hot_tracker_report_service
from app.services.ai_hot_tracker_report_service import generate_ai_hot_tracker_report
from app.services.model_interface_service import ModelInterfaceError


class FakeJsonModelInterface:
    def __init__(self, responses: list[dict[str, object]] | dict[str, object]) -> None:
        if isinstance(responses, dict):
            self._responses = [responses]
        else:
            self._responses = responses
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
    return type("Workspace", (), {"module_type": "research"})()


def _sample_items(generated_at: datetime) -> list[AiHotTrackerSourceItem]:
    return [
        AiHotTrackerSourceItem(
            id="source-1",
            source_id="framework-feed",
            source_label="Framework Feed",
            source_kind="atom_feed",
            category="frameworks",
            title="Framework Release 2.0",
            url="https://example.com/framework-2",
            summary="Added stronger model routing and tracing support.",
            published_at=generated_at,
            tags=["framework", "routing"],
        ),
        AiHotTrackerSourceItem(
            id="source-2",
            source_id="paper-feed",
            source_label="Paper Feed",
            source_kind="rss_feed",
            category="model_research",
            title="New Agent Training Paper",
            url="https://arxiv.org/abs/2604.00001",
            summary="Shows stronger coordination behavior.",
            published_at=generated_at,
            tags=["paper", "agent"],
        ),
    ]


def _mock_intake(monkeypatch: MonkeyPatch, intake_items: list[AiHotTrackerSourceItem]) -> None:
    monkeypatch.setattr(ai_hot_tracker_report_service.workspace_repository, "get_workspace", _mock_workspace)
    monkeypatch.setattr(
        ai_hot_tracker_report_service,
        "fetch_ai_hot_tracker_source_items",
        lambda: ai_hot_tracker_report_service.AiHotTrackerSourceIntakeResult(
            source_catalog=[
                AiHotTrackerSourceDefinition(
                    id="framework-feed",
                    label="Framework Feed",
                    category="frameworks",
                    source_kind="atom_feed",
                    feed_url="https://example.com/framework.atom",
                    tags=["framework"],
                )
            ],
            source_items=intake_items,
            source_failures=[
                AiHotTrackerSourceFailure(
                    source_id="vendor-feed",
                    source_label="Vendor Feed",
                    message="timeout",
                )
            ],
        ),
    )


def test_generate_ai_hot_tracker_report_builds_structured_output(monkeypatch: MonkeyPatch) -> None:
    generated_at = datetime(2026, 4, 16, 8, 0, tzinfo=UTC)
    intake_items = _sample_items(generated_at)
    _mock_intake(monkeypatch, intake_items)
    fake_interface = FakeJsonModelInterface(
        {
            "title": "框架与 Agent 训练都在加速",
            "frontier_summary": "本轮可信来源显示，框架发布与 agent 训练论文同时升温。",
            "trend_judgment": "短期内最值得继续看的是框架侧的路由能力和 agent 训练方法是否同步成熟。",
            "themes": [
                {"label": "Agent", "summary": "Agent 训练与执行链正在继续上行。"}
            ],
            "events": [
                {
                    "title": "Framework Release 2.0",
                    "summary": "框架发布强化了路由与 tracing。",
                    "significance": "这会直接影响工程选型。",
                    "source_item_ids": ["source-1"],
                }
            ],
            "project_cards": [
                {
                    "title": "Framework Release 2.0",
                    "summary": "这次发布补强了模型路由可见性。",
                    "why_it_matters": "更适合做复杂 agent 工作流。",
                    "source_item_ids": ["source-1"],
                    "tags": ["framework", "routing"],
                }
            ],
            "reference_item_ids": ["source-1", "source-2"],
        }
    )
    monkeypatch.setattr(ai_hot_tracker_report_service, "get_chat_model_interface", lambda: fake_interface)

    result = generate_ai_hot_tracker_report(workspace_id="workspace-1", user_id="user-1")

    assert result.title == "框架与 Agent 训练都在加速"
    assert result.output.frontier_summary.startswith("本轮可信来源显示")
    assert result.output.project_cards[0].source_label == "Framework Feed"
    assert result.output.project_cards[0].official_url == "https://example.com/framework-2"
    assert result.output.reference_sources[0].url == "https://example.com/framework-2"
    assert result.output.reference_sources[1].source_kind == "paper"
    assert result.degraded_reason == "source_intake_partial"
    assert result.source_set["mode"] == "ai_hot_tracker_structured_report"
    assert len(fake_interface.calls) == 1


def test_generate_ai_hot_tracker_report_repairs_invalid_first_draft(monkeypatch: MonkeyPatch) -> None:
    generated_at = datetime(2026, 4, 16, 8, 0, tzinfo=UTC)
    intake_items = _sample_items(generated_at)
    _mock_intake(monkeypatch, intake_items)
    fake_interface = FakeJsonModelInterface(
        [
            {
                "title": "框架与 Agent 训练都在加速",
                "frontier_summary": "本轮可信来源显示，框架发布与 agent 训练论文同时升温。",
                "trend_judgment": "短期内最值得继续看的是框架侧的路由能力和 agent 训练方法是否同步成熟。",
                "themes": [{"label": "Agent", "summary": "Agent 训练与执行链正在继续上行。"}],
                "events": [
                    {
                        "title": "Framework Release 2.0",
                        "summary": "框架发布强化了路由与 tracing。",
                        "significance": "这会直接影响工程选型。",
                        "source_item_ids": ["source-1"],
                    }
                ],
                "project_cards": [
                    {
                        "title": "Broken Card",
                    }
                ],
            },
            {
                "title": "框架与 Agent 训练都在加速",
                "frontier_summary": "本轮可信来源显示，框架发布与 agent 训练论文同时升温。",
                "trend_judgment": "短期内最值得继续看的是框架侧的路由能力和 agent 训练方法是否同步成熟。",
                "themes": [{"label": "Agent", "summary": "Agent 训练与执行链正在继续上行。"}],
                "events": [
                    {
                        "title": "Framework Release 2.0",
                        "summary": "框架发布强化了路由与 tracing。",
                        "significance": "这会直接影响工程选型。",
                        "source_item_ids": ["source-1"],
                    }
                ],
                "project_cards": [
                    {
                        "title": "Framework Release 2.0",
                        "summary": "这次发布补强了模型路由可见性。",
                        "why_it_matters": "更适合做复杂 agent 工作流。",
                        "source_item_ids": ["source-1"],
                        "tags": ["framework", "routing"],
                    }
                ],
                "reference_item_ids": ["source-1"],
            },
        ]
    )
    monkeypatch.setattr(ai_hot_tracker_report_service, "get_chat_model_interface", lambda: fake_interface)

    result = generate_ai_hot_tracker_report(workspace_id="workspace-1", user_id="user-1")

    assert result.title == "框架与 Agent 训练都在加速"
    assert result.output.project_cards
    assert result.output.reference_sources[0].url == "https://example.com/framework-2"
    assert len(fake_interface.calls) == 2


def test_generate_ai_hot_tracker_report_returns_degraded_response_when_model_generation_keeps_failing(
    monkeypatch: MonkeyPatch,
) -> None:
    generated_at = datetime(2026, 4, 16, 8, 0, tzinfo=UTC)
    intake_items = _sample_items(generated_at)
    _mock_intake(monkeypatch, intake_items)
    monkeypatch.setattr(ai_hot_tracker_report_service, "get_chat_model_interface", lambda: FailingJsonModelInterface())

    result = generate_ai_hot_tracker_report(workspace_id="workspace-1", user_id="user-1")

    assert result.degraded_reason == "report_generation_failed"
    assert result.title == "本轮热点暂不可用"
    assert "结构化报告还没有成功生成" in result.output.frontier_summary


def test_generate_ai_hot_tracker_report_returns_degraded_response_when_no_items(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(ai_hot_tracker_report_service.workspace_repository, "get_workspace", _mock_workspace)
    monkeypatch.setattr(
        ai_hot_tracker_report_service,
        "fetch_ai_hot_tracker_source_items",
        lambda: ai_hot_tracker_report_service.AiHotTrackerSourceIntakeResult(
            source_catalog=[],
            source_items=[],
            source_failures=[],
        ),
    )

    result = generate_ai_hot_tracker_report(workspace_id="workspace-1", user_id="user-1")

    assert result.degraded_reason == "source_intake_unavailable"
    assert result.title == "本轮热点暂不可用"
    assert "暂时无法生成有效报告" in result.output.frontier_summary
