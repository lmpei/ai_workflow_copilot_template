from __future__ import annotations

import hashlib
import html
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import httpx

from app.schemas.ai_frontier_research import (
    AiHotTrackerSourceDefinition,
    AiHotTrackerSourceFailure,
    AiHotTrackerSourceItem,
)

DEFAULT_AI_HOT_TRACKER_SOURCE_CATALOG: tuple[AiHotTrackerSourceDefinition, ...] = (
    AiHotTrackerSourceDefinition(
        id="arxiv-cs-ai",
        label="arXiv cs.AI",
        category="model_research",
        source_kind="rss_feed",
        feed_url="https://export.arxiv.org/rss/cs.AI",
        site_url="https://arxiv.org/list/cs.AI/recent",
        tags=["paper", "research", "models"],
    ),
    AiHotTrackerSourceDefinition(
        id="arxiv-cs-lg",
        label="arXiv cs.LG",
        category="model_research",
        source_kind="rss_feed",
        feed_url="https://export.arxiv.org/rss/cs.LG",
        site_url="https://arxiv.org/list/cs.LG/recent",
        tags=["paper", "research", "training"],
    ),
    AiHotTrackerSourceDefinition(
        id="huggingface-transformers",
        label="Transformers Releases",
        category="frameworks",
        source_kind="atom_feed",
        feed_url="https://github.com/huggingface/transformers/releases.atom",
        site_url="https://github.com/huggingface/transformers/releases",
        tags=["framework", "open-source", "nlp"],
    ),
    AiHotTrackerSourceDefinition(
        id="vllm-releases",
        label="vLLM Releases",
        category="inference_runtime",
        source_kind="atom_feed",
        feed_url="https://github.com/vllm-project/vllm/releases.atom",
        site_url="https://github.com/vllm-project/vllm/releases",
        tags=["serving", "inference", "open-source"],
    ),
    AiHotTrackerSourceDefinition(
        id="ollama-releases",
        label="Ollama Releases",
        category="local_runtime",
        source_kind="atom_feed",
        feed_url="https://github.com/ollama/ollama/releases.atom",
        site_url="https://github.com/ollama/ollama/releases",
        tags=["local", "runtime", "open-source"],
    ),
    AiHotTrackerSourceDefinition(
        id="langchain-releases",
        label="LangChain Releases",
        category="agent_frameworks",
        source_kind="atom_feed",
        feed_url="https://github.com/langchain-ai/langchain/releases.atom",
        site_url="https://github.com/langchain-ai/langchain/releases",
        tags=["agent", "workflow", "framework"],
    ),
)


class AiHotTrackerSourceFetchError(Exception):
    pass


@dataclass(slots=True)
class AiHotTrackerSourceIntakeResult:
    source_catalog: list[AiHotTrackerSourceDefinition]
    source_items: list[AiHotTrackerSourceItem]
    source_failures: list[AiHotTrackerSourceFailure]


_TAG_PATTERN = re.compile(r"<[^>]+>")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def list_ai_hot_tracker_source_catalog() -> list[AiHotTrackerSourceDefinition]:
    return [source.model_copy(deep=True) for source in DEFAULT_AI_HOT_TRACKER_SOURCE_CATALOG]


def fetch_ai_hot_tracker_source_items(
    *,
    limit_per_source: int = 4,
    total_limit: int = 18,
    timeout: float = 12.0,
) -> AiHotTrackerSourceIntakeResult:
    source_catalog = list_ai_hot_tracker_source_catalog()
    source_items: list[AiHotTrackerSourceItem] = []
    source_failures: list[AiHotTrackerSourceFailure] = []

    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        for source in source_catalog:
            try:
                response = client.get(source.feed_url)
                response.raise_for_status()
                parsed_items = _parse_source_feed(source=source, payload=response.text)
                source_items.extend(parsed_items[: max(1, limit_per_source)])
            except Exception as error:  # pragma: no cover - exercised through tests via mocks
                source_failures.append(
                    AiHotTrackerSourceFailure(
                        source_id=source.id,
                        source_label=source.label,
                        message=str(error),
                    )
                )

    ordered_items = sorted(
        _dedupe_source_items(source_items),
        key=lambda item: item.published_at or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )
    return AiHotTrackerSourceIntakeResult(
        source_catalog=source_catalog,
        source_items=ordered_items[: max(1, total_limit)],
        source_failures=source_failures,
    )


def _parse_source_feed(
    *,
    source: AiHotTrackerSourceDefinition,
    payload: str,
) -> list[AiHotTrackerSourceItem]:
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError as error:  # pragma: no cover - validated in tests
        raise AiHotTrackerSourceFetchError(f"Failed to parse {source.label} feed") from error

    if root.tag.endswith("feed"):
        return _parse_atom_feed(source=source, root=root)
    return _parse_rss_feed(source=source, root=root)


def _parse_atom_feed(
    *,
    source: AiHotTrackerSourceDefinition,
    root: ElementTree.Element,
) -> list[AiHotTrackerSourceItem]:
    items: list[AiHotTrackerSourceItem] = []
    for entry in root.findall("{*}entry"):
        title = _clean_text(_find_text(entry, "{*}title"))
        url = _find_atom_link(entry)
        summary = _clean_text(_find_text(entry, "{*}summary") or _find_text(entry, "{*}content"))
        published_at = _parse_datetime(
            _find_text(entry, "{*}updated") or _find_text(entry, "{*}published")
        )
        raw_id = _find_text(entry, "{*}id") or url or title
        if not title or not url:
            continue
        items.append(
            AiHotTrackerSourceItem(
                id=_stable_item_id(source.id, raw_id),
                source_id=source.id,
                source_label=source.label,
                source_kind=source.source_kind,
                category=source.category,
                title=title,
                url=url,
                summary=summary or title,
                published_at=published_at,
                tags=list(source.tags),
            )
        )
    return items


def _parse_rss_feed(
    *,
    source: AiHotTrackerSourceDefinition,
    root: ElementTree.Element,
) -> list[AiHotTrackerSourceItem]:
    items: list[AiHotTrackerSourceItem] = []
    for entry in root.findall("./channel/item"):
        title = _clean_text(_find_text(entry, "title"))
        url = _clean_text(_find_text(entry, "link"))
        summary = _clean_text(_find_text(entry, "description"))
        published_at = _parse_datetime(_find_text(entry, "pubDate"))
        raw_id = _find_text(entry, "guid") or url or title
        if not title or not url:
            continue
        items.append(
            AiHotTrackerSourceItem(
                id=_stable_item_id(source.id, raw_id),
                source_id=source.id,
                source_label=source.label,
                source_kind=source.source_kind,
                category=source.category,
                title=title,
                url=url,
                summary=summary or title,
                published_at=published_at,
                tags=list(source.tags),
            )
        )
    return items


def _find_text(element: ElementTree.Element, selector: str) -> str | None:
    child = element.find(selector)
    if child is None or child.text is None:
        return None
    return child.text


def _find_atom_link(entry: ElementTree.Element) -> str | None:
    for child in entry.findall("{*}link"):
        href = child.attrib.get("href")
        rel = child.attrib.get("rel")
        if href and rel in {None, "", "alternate"}:
            return href
    return None


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    normalized = value.strip()
    if not normalized:
        return None

    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(normalized)
        except (TypeError, ValueError):
            return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _clean_text(value: str | None) -> str:
    if not value:
        return ""

    stripped = html.unescape(_TAG_PATTERN.sub(" ", value))
    normalized = _WHITESPACE_PATTERN.sub(" ", stripped).strip()
    return normalized[:480]


def _stable_item_id(source_id: str, raw_id: str) -> str:
    digest = hashlib.sha1(f"{source_id}:{raw_id}".encode("utf-8")).hexdigest()
    return f"{source_id}-{digest[:12]}"


def _dedupe_source_items(items: list[AiHotTrackerSourceItem]) -> list[AiHotTrackerSourceItem]:
    deduped: list[AiHotTrackerSourceItem] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        key = (item.source_id, item.url)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped
