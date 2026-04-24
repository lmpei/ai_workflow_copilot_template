from datetime import UTC, datetime

import httpx
from pytest import MonkeyPatch

from app.schemas.ai_frontier_research import AiHotTrackerSourceDefinition
from app.services import ai_hot_tracker_source_service
from app.services.ai_hot_tracker_source_service import fetch_ai_hot_tracker_source_items


ATOM_PAYLOAD = """
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>tag:example.com,2026:1</id>
    <title>Framework Release 2.0</title>
    <updated>2026-04-15T08:00:00Z</updated>
    <summary>Added stronger model routing and tracing support.</summary>
    <link href="https://example.com/framework-2" />
  </entry>
  <entry>
    <id>tag:example.com,2026:0</id>
    <title>Framework Release 1.9</title>
    <updated>2026-04-10T08:00:00Z</updated>
    <summary>Earlier release.</summary>
    <link href="https://example.com/framework-1-9" />
  </entry>
</feed>
""".strip()

RSS_PAYLOAD = """
<rss version="2.0">
  <channel>
    <item>
      <guid>paper-1</guid>
      <title>New Agent Training Paper</title>
      <pubDate>Wed, 16 Apr 2026 08:00:00 GMT</pubDate>
      <description>Shows stronger coordination behavior.</description>
      <link>https://arxiv.org/abs/2604.00001</link>
    </item>
  </channel>
</rss>
""".strip()


class FakeResponse:
    def __init__(self, text: str, status_code: int = 200) -> None:
        self.text = text
        self.status_code = status_code
        self.request = httpx.Request("GET", "https://example.com/feed")

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("boom", request=self.request, response=httpx.Response(self.status_code))


class FakeClient:
    def __init__(self, mapping: dict[str, str | Exception]) -> None:
        self.mapping = mapping

    def __enter__(self) -> "FakeClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def get(self, url: str, **_: object) -> FakeResponse:
        payload = self.mapping[url]
        if isinstance(payload, Exception):
            raise payload
        return FakeResponse(payload)


def test_fetch_ai_hot_tracker_source_items_parses_and_sorts_feeds(monkeypatch: MonkeyPatch) -> None:
    source_catalog = [
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
    ]
    monkeypatch.setattr(ai_hot_tracker_source_service, "list_ai_hot_tracker_source_catalog", lambda: source_catalog)
    monkeypatch.setattr(
        ai_hot_tracker_source_service.httpx,
        "Client",
        lambda **kwargs: FakeClient(
            {
                "https://example.com/framework.atom": ATOM_PAYLOAD,
                "https://example.com/papers.rss": RSS_PAYLOAD,
            }
        ),
    )

    result = fetch_ai_hot_tracker_source_items(limit_per_source=2, total_limit=4)

    assert result.source_failures == []
    assert [item.title for item in result.source_items] == [
        "New Agent Training Paper",
        "Framework Release 2.0",
        "Framework Release 1.9",
    ]
    assert result.source_items[0].published_at == datetime(2026, 4, 16, 8, 0, tzinfo=UTC)
    assert result.source_items[0].source_label == "Paper Feed"
    assert result.source_items[1].url == "https://example.com/framework-2"


def test_fetch_ai_hot_tracker_source_items_records_failures(monkeypatch: MonkeyPatch) -> None:
    source_catalog = [
        AiHotTrackerSourceDefinition(
            id="broken-feed",
            label="Broken Feed",
            category="frameworks",
            source_kind="atom_feed",
            feed_url="https://example.com/broken.atom",
            tags=["framework"],
        )
    ]
    monkeypatch.setattr(ai_hot_tracker_source_service, "list_ai_hot_tracker_source_catalog", lambda: source_catalog)
    monkeypatch.setattr(
        ai_hot_tracker_source_service.httpx,
        "Client",
        lambda **kwargs: FakeClient(
            {
                "https://example.com/broken.atom": RuntimeError("network down"),
            }
        ),
    )

    result = fetch_ai_hot_tracker_source_items(limit_per_source=2, total_limit=4)

    assert result.source_items == []
    assert len(result.source_failures) == 1
    assert result.source_failures[0].source_id == "broken-feed"
    assert "network down" in result.source_failures[0].message
