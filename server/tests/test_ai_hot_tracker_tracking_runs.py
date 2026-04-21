from datetime import UTC, datetime

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.schemas.ai_frontier_research import (
    AiHotTrackerSourceDefinition,
    AiHotTrackerSourceFailure,
    AiHotTrackerSourceItem,
)
from app.services import ai_hot_tracker_follow_up_service, ai_hot_tracker_report_service, ai_hot_tracker_tracking_service


def _register_and_login(client: TestClient, *, email: str, name: str) -> dict[str, str]:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "super-secret",
            "name": name,
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "super-secret",
        },
    )
    assert login_response.status_code == 200
    return {"token": login_response.json()["access_token"]}


def _create_workspace(client: TestClient, token: str) -> str:
    response = client.post(
        "/api/v1/workspaces",
        json={"name": "AI 热点追踪", "module_type": "research"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _build_intake(now: datetime, *items: AiHotTrackerSourceItem):
    return ai_hot_tracker_report_service.AiHotTrackerSourceIntakeResult(
        source_catalog=[
            AiHotTrackerSourceDefinition(
                id="framework-feed",
                label="Framework Feed",
                category="frameworks",
                source_kind="atom_feed",
                feed_url="https://example.com/framework.atom",
                tags=["framework"],
            ),
            AiHotTrackerSourceDefinition(
                id="paper-feed",
                label="Paper Feed",
                category="model_research",
                source_kind="rss_feed",
                feed_url="https://example.com/papers.rss",
                tags=["paper"],
            ),
        ],
        source_items=list(items),
        source_failures=[
            AiHotTrackerSourceFailure(
                source_id="vendor-feed",
                source_label="Vendor Feed",
                message="timeout",
            )
        ]
        if items
        else [],
    )


def _build_item(
    *,
    item_id: str,
    source_id: str,
    source_label: str,
    category: str,
    title: str,
    url: str,
    summary: str,
    published_at: datetime,
) -> AiHotTrackerSourceItem:
    return AiHotTrackerSourceItem(
        id=item_id,
        source_id=source_id,
        source_label=source_label,
        source_kind="atom_feed" if source_id == "framework-feed" else "rss_feed",
        category=category,
        title=title,
        url=url,
        summary=summary,
        published_at=published_at,
        tags=["agent"] if source_id == "paper-feed" else ["framework"],
    )


class FakeJsonModelInterface:
    def __init__(self, responses: list[dict[str, object]] | dict[str, object]) -> None:
        self._responses = [responses] if isinstance(responses, dict) else responses

    def generate_json_object(self, **kwargs):
        from app.services.model_interface_service import ModelJsonResponse, ModelUsage

        if not self._responses:
            raise AssertionError("No more fake JSON responses configured")

        return ModelJsonResponse(
            data=self._responses.pop(0),
            text="{}",
            usage=ModelUsage(input_tokens=12, output_tokens=18, total_tokens=30),
        )


class FakeTextModelInterface:
    def generate_text(self, **kwargs):
        from app.services.model_interface_service import ModelTextResponse, ModelUsage

        return ModelTextResponse(
            text="这轮重点在工程框架与 agent 研究是否同步成熟。【来源：Framework Feed · Framework Release 3.0】",
            usage=ModelUsage(input_tokens=18, output_tokens=24, total_tokens=42),
        )


def test_ai_hot_tracker_runs_persist_and_diff_between_rounds(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])
    now = datetime(2026, 4, 21, 8, 0, tzinfo=UTC)

    first_intake = _build_intake(
        now,
        _build_item(
            item_id="source-1",
            source_id="framework-feed",
            source_label="Framework Feed",
            category="frameworks",
            title="Framework Release 2.0",
            url="https://example.com/framework-2",
            summary="Added routing and tracing support.",
            published_at=now,
        ),
        _build_item(
            item_id="source-2",
            source_id="paper-feed",
            source_label="Paper Feed",
            category="model_research",
            title="New Agent Training Paper",
            url="https://arxiv.org/abs/2604.00001",
            summary="Shows stronger coordination behavior.",
            published_at=now,
        ),
    )
    second_intake = _build_intake(
        now,
        _build_item(
            item_id="source-2",
            source_id="paper-feed",
            source_label="Paper Feed",
            category="model_research",
            title="New Agent Training Paper",
            url="https://arxiv.org/abs/2604.00001",
            summary="Shows stronger coordination behavior.",
            published_at=now,
        ),
        _build_item(
            item_id="source-3",
            source_id="framework-feed",
            source_label="Framework Feed",
            category="frameworks",
            title="Framework Release 3.0",
            url="https://example.com/framework-3",
            summary="Adds stronger memory orchestration.",
            published_at=now,
        ),
    )
    intakes = [first_intake, second_intake]

    monkeypatch.setattr(
        ai_hot_tracker_tracking_service,
        "fetch_ai_hot_tracker_source_items",
        lambda total_limit=18: intakes.pop(0),
    )
    monkeypatch.setattr(
        ai_hot_tracker_report_service,
        "get_chat_model_interface",
        lambda: FakeJsonModelInterface(
            {
                "title": "工程框架与 Agent 研究升温",
                "frontier_summary": "本轮可信来源显示，工程框架与 agent 研究都在继续升温。",
                "trend_judgment": "最值得继续看的，是工程能力是否能承接 agent 复杂度。",
                "themes": [{"label": "Agent", "summary": "Agent 训练与执行链路继续推进。"}],
                "events": [
                    {
                        "title": "Framework Release",
                        "summary": "框架继续发布新版本。",
                        "significance": "这会影响工程选型。",
                        "source_item_ids": ["source-3", "source-1"],
                    }
                ],
                "project_cards": [
                    {
                        "title": "Framework",
                        "summary": "框架版本持续推进。",
                        "why_it_matters": "对工作流编排更重要。",
                        "source_item_ids": ["source-3", "source-1"],
                        "tags": ["framework"],
                    }
                ],
                "reference_item_ids": ["source-3", "source-2", "source-1"],
            }
        ),
    )

    first_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/ai-hot-tracker/runs",
        headers=headers,
    )
    assert first_response.status_code == 201
    first_run = first_response.json()
    assert first_run["status"] == "completed"
    assert first_run["delta"]["change_state"] == "first_run"
    assert first_run["delta"]["new_item_count"] == 2

    second_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/ai-hot-tracker/runs",
        headers=headers,
    )
    assert second_response.status_code == 201
    second_run = second_response.json()
    assert second_run["previous_run_id"] == first_run["id"]
    assert second_run["delta"]["change_state"] == "meaningful_update"
    assert second_run["delta"]["new_item_count"] == 1
    assert second_run["delta"]["continuing_item_count"] == 1
    assert second_run["delta"]["cooled_down_item_count"] == 1
    assert second_run["delta"]["new_titles"] == ["Framework Release 3.0"]

    list_response = client.get(
        f"/api/v1/workspaces/{workspace_id}/ai-hot-tracker/runs",
        headers=headers,
    )
    assert list_response.status_code == 200
    listed = list_response.json()
    assert [item["id"] for item in listed] == [second_run["id"], first_run["id"]]


def test_ai_hot_tracker_run_follow_up_is_bound_and_persisted(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])
    now = datetime(2026, 4, 21, 8, 0, tzinfo=UTC)

    monkeypatch.setattr(
        ai_hot_tracker_tracking_service,
        "fetch_ai_hot_tracker_source_items",
        lambda total_limit=18: _build_intake(
            now,
            _build_item(
                item_id="source-3",
                source_id="framework-feed",
                source_label="Framework Feed",
                category="frameworks",
                title="Framework Release 3.0",
                url="https://example.com/framework-3",
                summary="Adds stronger memory orchestration.",
                published_at=now,
            ),
        ),
    )
    monkeypatch.setattr(
        ai_hot_tracker_report_service,
        "get_chat_model_interface",
        lambda: FakeJsonModelInterface(
            {
                "title": "框架继续推进",
                "frontier_summary": "框架能力还在快速推进。",
                "trend_judgment": "下一步重点看工程能力是否稳定。",
                "themes": [{"label": "框架", "summary": "框架迭代仍然密集。"}],
                "events": [
                    {
                        "title": "Framework Release 3.0",
                        "summary": "新增 memory orchestration。",
                        "significance": "会影响复杂工作流。",
                        "source_item_ids": ["source-3"],
                    }
                ],
                "project_cards": [
                    {
                        "title": "Framework Release 3.0",
                        "summary": "补强 memory orchestration。",
                        "why_it_matters": "更适合持续追踪场景。",
                        "source_item_ids": ["source-3"],
                        "tags": ["framework"],
                    }
                ],
                "reference_item_ids": ["source-3"],
            }
        ),
    )
    monkeypatch.setattr(
        ai_hot_tracker_follow_up_service,
        "get_chat_model_interface",
        lambda: FakeTextModelInterface(),
    )

    run_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/ai-hot-tracker/runs",
        headers=headers,
    )
    assert run_response.status_code == 201
    run_id = run_response.json()["id"]

    follow_up_response = client.post(
        f"/api/v1/ai-hot-tracker/runs/{run_id}/follow-up",
        json={"question": "为什么这轮更重要？", "focus_label": "Framework Release 3.0"},
        headers=headers,
    )
    assert follow_up_response.status_code == 200
    assert "Framework Feed" in follow_up_response.json()["answer"]

    run_detail = client.get(f"/api/v1/ai-hot-tracker/runs/{run_id}", headers=headers)
    assert run_detail.status_code == 200
    assert len(run_detail.json()["follow_ups"]) == 1
    assert run_detail.json()["follow_ups"][0]["question"] == "为什么这轮更重要？"
