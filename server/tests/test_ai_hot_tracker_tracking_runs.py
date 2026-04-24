from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.repositories import ai_hot_tracker_tracking_state_repository
from app.schemas.ai_frontier_research import (
    AiHotTrackerSourceDefinition,
    AiHotTrackerSourceFailure,
    AiHotTrackerSourceItem,
)
from app.services import (
    ai_hot_tracker_follow_up_service,
    ai_hot_tracker_report_service,
    ai_hot_tracker_tracking_service,
)


def _register_and_login(client: TestClient, *, email: str, name: str) -> dict[str, str]:
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "super-secret", "name": name},
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "super-secret"},
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


def _build_intake(*items: AiHotTrackerSourceItem):
    return ai_hot_tracker_report_service.AiHotTrackerSourceIntakeResult(
        source_catalog=[
            AiHotTrackerSourceDefinition(
                id="openai-news",
                label="OpenAI News",
                category="models",
                source_family="official",
                source_kind="html_list",
                feed_url="https://openai.com/news/",
                tags=["model", "product", "agent", "chatgpt"],
                audience_tags=["ordinary_user", "product_builder"],
                authority_weight=0.92,
            ),
            AiHotTrackerSourceDefinition(
                id="arxiv-cs-ai",
                label="arXiv cs.AI",
                category="research",
                source_family="research",
                source_kind="rss_feed",
                feed_url="https://example.com/papers.rss",
                tags=["paper", "agent"],
                audience_tags=["learner", "developer"],
                authority_weight=0.78,
            ),
        ],
        source_items=list(items),
        source_failures=[
            AiHotTrackerSourceFailure(
                source_id="openai-news",
                source_label="OpenAI News",
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
    source_family: str = "official",
) -> AiHotTrackerSourceItem:
    return AiHotTrackerSourceItem(
        id=item_id,
        source_id=source_id,
        source_label=source_label,
        source_kind="html_list" if source_id == "openai-news" else "rss_feed",
        category=category,
        source_family=source_family,
        title=title,
        url=url,
        summary=summary,
        published_at=published_at,
        tags=["agent", "chatgpt"] if source_id == "openai-news" else ["paper", "agent"],
        audience_tags=["ordinary_user", "product_builder"]
        if source_id == "openai-news"
        else ["learner", "developer"],
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
            text="这件事重要，因为 ChatGPT agent tools 会改变用户对 AI 助手的预期。【来源：OpenAI News】",
            usage=ModelUsage(input_tokens=18, output_tokens=24, total_tokens=42),
        )


def _brief_payload(*signal_ids: str) -> dict[str, object]:
    primary_source_id = signal_ids[0] if signal_ids else "source-1"
    secondary_source_id = signal_ids[1] if len(signal_ids) > 1 else primary_source_id
    return {
        "headline": "ChatGPT agent tools are the clearest signal this round",
        "summary": "This round shows AI products moving toward direct task execution.",
        "change_state": "meaningful_update",
        "signals": [
            {
                "title": "ChatGPT agent tools move into product use",
                "summary": "OpenAI is pushing ChatGPT closer to action-oriented assistance.",
                "why_now": "This changes what mainstream users can expect from AI assistants.",
                "impact": "普通用户可能会更早遇到能执行任务的 AI 产品，而不只是问答工具。",
                "audience": ["AI 用户", "产品人"],
                "change_type": "new",
                "priority_level": "high",
                "source_item_ids": [primary_source_id],
            }
        ],
        "keep_watching": [
            {
                "title": "Agent training direction",
                "reason": "The research signal is strengthening but needs product confirmation.",
                "source_item_ids": [secondary_source_id],
            }
        ],
    }


def test_ai_hot_tracker_runs_persist_and_diff_between_rounds(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])
    now = datetime(2026, 4, 21, 8, 0, tzinfo=UTC)

    first_intake = _build_intake(
        _build_item(
            item_id="source-1",
            source_id="openai-news",
            source_label="OpenAI News",
            category="models",
            title="OpenAI launches ChatGPT agent tools",
            url="https://openai.com/news/chatgpt-agent-tools",
            summary="OpenAI introduces agent tools for ChatGPT users.",
            published_at=now,
        ),
        _build_item(
            item_id="source-2",
            source_id="arxiv-cs-ai",
            source_label="arXiv cs.AI",
            category="research",
            source_family="research",
            title="New Agent Training Paper",
            url="https://arxiv.org/abs/2604.00001",
            summary="Shows stronger coordination behavior.",
            published_at=now,
        ),
    )
    second_intake = _build_intake(
        _build_item(
            item_id="source-2",
            source_id="arxiv-cs-ai",
            source_label="arXiv cs.AI",
            category="research",
            source_family="research",
            title="New Agent Training Paper",
            url="https://arxiv.org/abs/2604.00001",
            summary="Shows stronger coordination behavior.",
            published_at=now,
        ),
        _build_item(
            item_id="source-3",
            source_id="openai-news",
            source_label="OpenAI News",
            category="models",
            title="OpenAI launches ChatGPT agent tools for browsing",
            url="https://openai.com/news/chatgpt-agent-tools-browsing",
            summary="OpenAI expands agent tools into browsing-oriented tasks.",
            published_at=now,
        ),
    )
    intakes = [first_intake, second_intake]

    monkeypatch.setattr(
        ai_hot_tracker_tracking_service,
        "fetch_ai_hot_tracker_source_items",
        lambda total_limit=24: intakes.pop(0),
    )
    monkeypatch.setattr(
        ai_hot_tracker_report_service,
        "get_chat_model_interface",
        lambda: FakeJsonModelInterface(_brief_payload("source-3", "source-2")),
    )

    first_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/ai-hot-tracker/runs",
        headers=headers,
    )
    assert first_response.status_code == 201
    first_run = first_response.json()
    assert first_run["status"] == "completed"
    assert first_run["output"]["signals"][0]["impact"].startswith("普通用户")
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
        lambda total_limit=24: _build_intake(
            _build_item(
                item_id="source-3",
                source_id="openai-news",
                source_label="OpenAI News",
                category="models",
                title="OpenAI launches ChatGPT agent tools",
                url="https://openai.com/news/chatgpt-agent-tools",
                summary="OpenAI introduces agent tools for ChatGPT users.",
                published_at=now,
            ),
        ),
    )
    monkeypatch.setattr(
        ai_hot_tracker_report_service,
        "get_chat_model_interface",
        lambda: FakeJsonModelInterface(_brief_payload("source-3")),
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
        json={"question": "这对普通用户有什么影响？", "focus_label": "ChatGPT agent tools"},
        headers=headers,
    )
    assert follow_up_response.status_code == 200
    follow_up_payload = follow_up_response.json()
    assert "ChatGPT agent tools" in follow_up_payload["answer"]
    assert follow_up_payload["follow_up"]["grounding_source_item_ids"] == ["source-3"]
    assert len(follow_up_payload["follow_up"]["grounding_event_ids"]) == 1
    assert follow_up_payload["follow_up"]["grounding_notes"]

    run_detail = client.get(f"/api/v1/ai-hot-tracker/runs/{run_id}", headers=headers)
    assert run_detail.status_code == 200
    assert len(run_detail.json()["follow_ups"]) == 1
    assert run_detail.json()["follow_ups"][0]["question"] == "这对普通用户有什么影响？"
    assert run_detail.json()["follow_ups"][0]["grounding_source_item_ids"] == ["source-3"]


def test_ai_hot_tracker_state_and_evaluation_endpoints_expose_runtime_context(
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
        lambda total_limit=24: _build_intake(
            _build_item(
                item_id="source-1",
                source_id="openai-news",
                source_label="OpenAI News",
                category="models",
                title="OpenAI launches ChatGPT agent tools",
                url="https://openai.com/news/chatgpt-agent-tools",
                summary="OpenAI introduces agent tools for ChatGPT users.",
                published_at=now,
            ),
            _build_item(
                item_id="source-2",
                source_id="arxiv-cs-ai",
                source_label="arXiv cs.AI",
                category="research",
                source_family="research",
                title="New Agent Training Paper",
                url="https://arxiv.org/abs/2604.00001",
                summary="Shows stronger coordination behavior.",
                published_at=now,
            ),
        ),
    )
    monkeypatch.setattr(
        ai_hot_tracker_report_service,
        "get_chat_model_interface",
        lambda: FakeJsonModelInterface(_brief_payload("source-1", "source-2")),
    )

    run_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/ai-hot-tracker/runs",
        headers=headers,
    )
    assert run_response.status_code == 201
    run_id = run_response.json()["id"]

    state_response = client.get(
        f"/api/v1/workspaces/{workspace_id}/ai-hot-tracker/state",
        headers=headers,
    )
    assert state_response.status_code == 200
    state_payload = state_response.json()
    assert state_payload["workspace_id"] == workspace_id
    assert state_payload["latest_saved_run_id"] == run_id
    assert state_payload["latest_change_state"] == "first_run"
    assert state_payload["tracking_profile"]["cadence"] == "daily"
    assert state_payload["latest_saved_run_generated_at"] is not None
    assert state_payload["latest_meaningful_update_at"] is None

    evaluation_response = client.get(
        f"/api/v1/ai-hot-tracker/runs/{run_id}/evaluation",
        headers=headers,
    )
    assert evaluation_response.status_code == 200
    evaluation_payload = evaluation_response.json()
    assert evaluation_payload["run_id"] == run_id
    assert len(evaluation_payload["ranked_items"]) == 2
    assert len(evaluation_payload["clustered_signals"]) >= 1
    assert len(evaluation_payload["source_failures"]) == 1
    assert evaluation_payload["output"]["headline"] == "ChatGPT agent tools are the clearest signal this round"
    assert evaluation_payload["ranked_items"][0]["score_breakdown"]["impact"] > 0
    assert evaluation_payload["delta"]["change_state"] == "first_run"
    assert evaluation_payload["quality_checks"]


def test_ai_hot_tracker_replay_evaluation_endpoint_exposes_suite_summary(
    client: TestClient,
) -> None:
    auth = _register_and_login(client, email="replay@example.com", name="Replay")
    headers = {"Authorization": f"Bearer {auth['token']}"}

    replay_response = client.get(
        "/api/v1/ai-hot-tracker/replay-evaluation",
        headers=headers,
    )
    assert replay_response.status_code == 200
    replay_payload = replay_response.json()
    assert replay_payload["status"] == "pass"
    assert replay_payload["total_case_count"] >= 5
    assert replay_payload["passed_case_count"] == replay_payload["total_case_count"]
    assert replay_payload["failed_case_count"] == 0
    assert replay_payload["cases"]
    assert replay_payload["cases"][0]["steps"]


def test_ai_hot_tracker_sweeper_skips_manual_cadence_workspaces(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    patch_response = client.patch(
        f"/api/v1/workspaces/{workspace_id}",
        json={
            "module_config_json": {
                "tracking_profile": {
                    "cadence": "manual",
                    "enabled_categories": ["models"],
                    "alert_threshold": 1,
                }
            }
        },
        headers=headers,
    )
    assert patch_response.status_code == 200

    called = {"count": 0}

    def _unexpected_fetch(total_limit=24):
        called["count"] += 1
        raise AssertionError("manual cadence workspaces should not be swept")

    monkeypatch.setattr(ai_hot_tracker_tracking_service, "fetch_ai_hot_tracker_source_items", _unexpected_fetch)

    result = ai_hot_tracker_tracking_service.run_ai_hot_tracker_tracking_sweeper()

    assert result["processed_workspace_count"] == 0
    assert called["count"] == 0


def test_ai_hot_tracker_sweeper_saves_first_run_and_skips_steady_state_history(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])
    now = datetime(2026, 4, 21, 8, 0, tzinfo=UTC)

    first_intake = _build_intake(
        _build_item(
            item_id="source-3",
            source_id="openai-news",
            source_label="OpenAI News",
            category="models",
            title="OpenAI launches ChatGPT agent tools",
            url="https://openai.com/news/chatgpt-agent-tools",
            summary="OpenAI introduces agent tools for ChatGPT users.",
            published_at=now,
        ),
    )
    repeated_intake = _build_intake(
        _build_item(
            item_id="source-3",
            source_id="openai-news",
            source_label="OpenAI News",
            category="models",
            title="OpenAI launches ChatGPT agent tools",
            url="https://openai.com/news/chatgpt-agent-tools",
            summary="OpenAI introduces agent tools for ChatGPT users.",
            published_at=now,
        ),
    )
    intakes = [first_intake, repeated_intake]

    monkeypatch.setattr(
        ai_hot_tracker_tracking_service,
        "fetch_ai_hot_tracker_source_items",
        lambda total_limit=24: intakes.pop(0),
    )
    monkeypatch.setattr(
        ai_hot_tracker_report_service,
        "get_chat_model_interface",
        lambda: FakeJsonModelInterface(_brief_payload("source-3")),
    )

    first_sweep = ai_hot_tracker_tracking_service.run_ai_hot_tracker_tracking_sweeper()
    assert first_sweep["saved_run_count"] == 1

    runs_after_first_sweep = client.get(
        f"/api/v1/workspaces/{workspace_id}/ai-hot-tracker/runs",
        headers=headers,
    )
    assert runs_after_first_sweep.status_code == 200
    assert len(runs_after_first_sweep.json()) == 1

    state = ai_hot_tracker_tracking_state_repository.get_ai_hot_tracker_tracking_state(
        workspace_id=workspace_id
    )
    assert state is not None
    ai_hot_tracker_tracking_state_repository.upsert_ai_hot_tracker_tracking_state(
        workspace_id=workspace_id,
        last_checked_at=state.last_checked_at,
        last_evaluated_at=state.last_evaluated_at,
        last_successful_scan_at=state.last_successful_scan_at,
        next_due_at=now - timedelta(minutes=1),
        last_cluster_snapshot_json=state.last_cluster_snapshot_json,
        last_saved_run_id=state.last_saved_run_id,
        last_notified_run_id=state.last_notified_run_id,
        latest_saved_run_generated_at=state.latest_saved_run_generated_at,
        latest_meaningful_update_at=state.latest_meaningful_update_at,
        consecutive_failure_count=state.consecutive_failure_count,
        last_error_message=state.last_error_message,
    )

    second_sweep = ai_hot_tracker_tracking_service.run_ai_hot_tracker_tracking_sweeper()
    assert second_sweep["saved_run_count"] == 0

    runs_after_second_sweep = client.get(
        f"/api/v1/workspaces/{workspace_id}/ai-hot-tracker/runs",
        headers=headers,
    )
    assert runs_after_second_sweep.status_code == 200
    assert len(runs_after_second_sweep.json()) == 1

    refreshed_state = ai_hot_tracker_tracking_state_repository.get_ai_hot_tracker_tracking_state(
        workspace_id=workspace_id
    )
    assert refreshed_state is not None
    assert refreshed_state.latest_saved_run_generated_at is not None

