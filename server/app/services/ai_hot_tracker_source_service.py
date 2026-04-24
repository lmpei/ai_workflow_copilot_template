from __future__ import annotations

import hashlib
import html
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.parse import urljoin
from xml.etree import ElementTree

import httpx

from app.schemas.ai_frontier_research import (
    AiHotTrackerSourceDefinition,
    AiHotTrackerSourceFailure,
    AiHotTrackerSourceItem,
)

DEFAULT_AI_HOT_TRACKER_SOURCE_CATALOG: tuple[AiHotTrackerSourceDefinition, ...] = (
    AiHotTrackerSourceDefinition(
        id="openai-news",
        label="OpenAI News",
        category="models",
        source_family="official",
        source_kind="html_list",
        feed_url="https://openai.com/news/",
        site_url="https://openai.com/news/",
        tags=["model", "product", "openai"],
        audience_tags=["ordinary_user", "product_builder", "developer"],
        authority_weight=0.92,
    ),
    AiHotTrackerSourceDefinition(
        id="anthropic-news",
        label="Anthropic News",
        category="models",
        source_family="official",
        source_kind="html_list",
        feed_url="https://www.anthropic.com/news",
        site_url="https://www.anthropic.com/news",
        tags=["model", "product", "anthropic", "claude"],
        audience_tags=["ordinary_user", "product_builder", "developer"],
        authority_weight=0.90,
    ),
    AiHotTrackerSourceDefinition(
        id="google-ai-blog",
        label="Google AI Blog",
        category="products",
        source_family="official",
        source_kind="html_list",
        feed_url="https://blog.google/technology/ai/",
        site_url="https://blog.google/technology/ai/",
        tags=["model", "product", "google", "gemini"],
        audience_tags=["ordinary_user", "product_builder", "learner"],
        authority_weight=0.88,
    ),
    AiHotTrackerSourceDefinition(
        id="meta-ai-blog",
        label="Meta AI Blog",
        category="models",
        source_family="official",
        source_kind="html_list",
        feed_url="https://ai.meta.com/blog/",
        site_url="https://ai.meta.com/blog/",
        tags=["model", "research", "meta", "llama"],
        audience_tags=["ordinary_user", "developer", "learner"],
        authority_weight=0.86,
    ),
    AiHotTrackerSourceDefinition(
        id="mistral-news",
        label="Mistral News",
        category="models",
        source_family="official",
        source_kind="html_list",
        feed_url="https://mistral.ai/news/",
        site_url="https://mistral.ai/news/",
        tags=["model", "product", "mistral"],
        audience_tags=["ordinary_user", "developer", "product_builder"],
        authority_weight=0.84,
    ),
    AiHotTrackerSourceDefinition(
        id="huggingface-blog",
        label="Hugging Face Blog",
        category="developer_tools",
        source_family="official",
        source_kind="rss_feed",
        feed_url="https://huggingface.co/blog/feed.xml",
        site_url="https://huggingface.co/blog",
        tags=["model", "developer", "open-source", "huggingface"],
        audience_tags=["developer", "learner", "product_builder"],
        authority_weight=0.82,
    ),
    AiHotTrackerSourceDefinition(
        id="arxiv-cs-ai",
        label="arXiv cs.AI",
        category="research",
        source_family="research",
        source_kind="rss_feed",
        feed_url="https://export.arxiv.org/rss/cs.AI",
        site_url="https://arxiv.org/list/cs.AI/recent",
        tags=["paper", "research", "models"],
        audience_tags=["learner", "developer"],
        authority_weight=0.78,
    ),
    AiHotTrackerSourceDefinition(
        id="arxiv-cs-lg",
        label="arXiv cs.LG",
        category="research",
        source_family="research",
        source_kind="rss_feed",
        feed_url="https://export.arxiv.org/rss/cs.LG",
        site_url="https://arxiv.org/list/cs.LG/recent",
        tags=["paper", "research", "training"],
        audience_tags=["learner", "developer"],
        authority_weight=0.78,
    ),
    AiHotTrackerSourceDefinition(
        id="huggingface-transformers",
        label="Transformers Releases",
        category="open_source",
        source_family="open_source",
        source_kind="atom_feed",
        feed_url="https://github.com/huggingface/transformers/releases.atom",
        site_url="https://github.com/huggingface/transformers/releases",
        tags=["framework", "open-source", "nlp", "transformers"],
        audience_tags=["developer", "learner"],
        authority_weight=0.82,
    ),
    AiHotTrackerSourceDefinition(
        id="vllm-releases",
        label="vLLM Releases",
        category="developer_tools",
        source_family="open_source",
        source_kind="atom_feed",
        feed_url="https://github.com/vllm-project/vllm/releases.atom",
        site_url="https://github.com/vllm-project/vllm/releases",
        tags=["serving", "inference", "open-source", "vllm"],
        audience_tags=["developer", "product_builder"],
        authority_weight=0.86,
    ),
    AiHotTrackerSourceDefinition(
        id="ollama-releases",
        label="Ollama Releases",
        category="products",
        source_family="open_source",
        source_kind="atom_feed",
        feed_url="https://github.com/ollama/ollama/releases.atom",
        site_url="https://github.com/ollama/ollama/releases",
        tags=["local", "runtime", "open-source", "ollama"],
        audience_tags=["ordinary_user", "developer", "learner"],
        authority_weight=0.74,
    ),
    AiHotTrackerSourceDefinition(
        id="langchain-releases",
        label="LangChain Releases",
        category="developer_tools",
        source_family="open_source",
        source_kind="atom_feed",
        feed_url="https://github.com/langchain-ai/langchain/releases.atom",
        site_url="https://github.com/langchain-ai/langchain/releases",
        tags=["agent", "workflow", "framework", "langchain"],
        audience_tags=["developer", "product_builder"],
        authority_weight=0.74,
    ),
    AiHotTrackerSourceDefinition(
        id="techcrunch-ai",
        label="TechCrunch AI",
        category="business",
        source_family="media",
        source_kind="rss_feed",
        feed_url="https://techcrunch.com/category/artificial-intelligence/feed/",
        site_url="https://techcrunch.com/category/artificial-intelligence/",
        tags=["business", "startup", "product", "media"],
        audience_tags=["ordinary_user", "product_builder"],
        authority_weight=0.66,
    ),
    AiHotTrackerSourceDefinition(
        id="the-verge-ai",
        label="The Verge AI",
        category="products",
        source_family="media",
        source_kind="rss_feed",
        feed_url="https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        site_url="https://www.theverge.com/ai-artificial-intelligence",
        tags=["product", "consumer", "media"],
        audience_tags=["ordinary_user", "learner"],
        authority_weight=0.64,
    ),
)


class AiHotTrackerSourceFetchError(Exception):
    pass


@dataclass(slots=True)
class AiHotTrackerSourceIntakeResult:
    source_catalog: list[AiHotTrackerSourceDefinition]
    source_items: list[AiHotTrackerSourceItem]
    source_failures: list[AiHotTrackerSourceFailure]


@dataclass(slots=True)
class _HtmlCandidate:
    title: str
    url: str
    summary: str = ""
    published_at: datetime | None = None


_TAG_PATTERN = re.compile(r"<[^>]+>")
_WHITESPACE_PATTERN = re.compile(r"\s+")
_ARTICLE_PATTERN = re.compile(r"<article\b[^>]*>.*?</article>", re.IGNORECASE | re.DOTALL)
_TIME_DATETIME_PATTERN = re.compile(
    r"<time\b[^>]*datetime=[\"']([^\"']+)[\"'][^>]*>",
    re.IGNORECASE | re.DOTALL,
)
_LINK_PATTERN = re.compile(
    r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
    re.IGNORECASE | re.DOTALL,
)
_PARAGRAPH_PATTERN = re.compile(r"<p\b[^>]*>(.*?)</p>", re.IGNORECASE | re.DOTALL)


class _FeedHtmlTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.parts.append(text)

    def text(self) -> str:
        return _clean_text(" ".join(self.parts))


def list_ai_hot_tracker_source_catalog() -> list[AiHotTrackerSourceDefinition]:
    return [source.model_copy(deep=True) for source in DEFAULT_AI_HOT_TRACKER_SOURCE_CATALOG]


def fetch_ai_hot_tracker_source_items(
    *,
    limit_per_source: int = 4,
    total_limit: int = 24,
    timeout: float = 12.0,
) -> AiHotTrackerSourceIntakeResult:
    source_catalog = list_ai_hot_tracker_source_catalog()
    source_items: list[AiHotTrackerSourceItem] = []
    source_failures: list[AiHotTrackerSourceFailure] = []

    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        for source in source_catalog:
            try:
                response = client.get(
                    source.feed_url,
                    headers={
                        "User-Agent": "LMPAI-Weave-AI-Hot-Tracker/1.0",
                        "Accept": "application/rss+xml, application/atom+xml, text/html;q=0.8",
                    },
                )
                response.raise_for_status()
                parsed_items = _parse_source_payload(source=source, payload=response.text)
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


def _parse_source_payload(
    *,
    source: AiHotTrackerSourceDefinition,
    payload: str,
) -> list[AiHotTrackerSourceItem]:
    if source.source_kind == "html_list":
        return _parse_html_list(source=source, payload=payload)
    return _parse_source_feed(source=source, payload=payload)


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
            _build_source_item(
                source=source,
                raw_id=raw_id,
                title=title,
                url=url,
                summary=summary or title,
                published_at=published_at,
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
            _build_source_item(
                source=source,
                raw_id=raw_id,
                title=title,
                url=url,
                summary=summary or title,
                published_at=published_at,
            )
        )
    return items


def _parse_html_list(
    *,
    source: AiHotTrackerSourceDefinition,
    payload: str,
) -> list[AiHotTrackerSourceItem]:
    candidates = _extract_json_ld_candidates(source=source, payload=payload)
    if not candidates:
        candidates = _extract_article_candidates(source=source, payload=payload)
    if not candidates:
        candidates = _extract_link_candidates(source=source, payload=payload)

    items: list[AiHotTrackerSourceItem] = []
    for candidate in candidates:
        if not candidate.title or not candidate.url:
            continue
        items.append(
            _build_source_item(
                source=source,
                raw_id=candidate.url,
                title=candidate.title,
                url=candidate.url,
                summary=candidate.summary or candidate.title,
                published_at=candidate.published_at,
            )
        )
    return items


def _extract_json_ld_candidates(
    *,
    source: AiHotTrackerSourceDefinition,
    payload: str,
) -> list[_HtmlCandidate]:
    candidates: list[_HtmlCandidate] = []
    for match in re.finditer(
        r"<script[^>]+application/ld\+json[^>]*>(.*?)</script>",
        payload,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        raw_json = html.unescape(match.group(1)).strip()
        try:
            parsed = json.loads(raw_json)
        except json.JSONDecodeError:
            continue
        candidates.extend(_walk_json_ld(source=source, value=parsed))
    return candidates


def _walk_json_ld(
    *,
    source: AiHotTrackerSourceDefinition,
    value: object,
) -> list[_HtmlCandidate]:
    if isinstance(value, list):
        return [
            candidate
            for item in value
            for candidate in _walk_json_ld(source=source, value=item)
        ]
    if not isinstance(value, dict):
        return []

    nested_items = value.get("itemListElement") or value.get("@graph")
    if nested_items:
        nested = _walk_json_ld(source=source, value=nested_items)
        if nested:
            return nested

    item = value.get("item") if isinstance(value.get("item"), dict) else value
    title = _clean_text(
        str(item.get("headline") or item.get("name") or item.get("title") or "")
    )
    url = str(item.get("url") or item.get("@id") or "")
    published_at = _parse_datetime(
        str(item.get("datePublished") or item.get("dateModified") or "")
    )
    description = _clean_text(str(item.get("description") or ""))
    if not title or not url:
        return []
    return [
        _HtmlCandidate(
            title=title,
            url=urljoin(source.feed_url, url),
            summary=description,
            published_at=published_at,
        )
    ]


def _extract_article_candidates(
    *,
    source: AiHotTrackerSourceDefinition,
    payload: str,
) -> list[_HtmlCandidate]:
    candidates: list[_HtmlCandidate] = []
    for block in _ARTICLE_PATTERN.findall(payload):
        link_match = _LINK_PATTERN.search(block)
        if link_match is None:
            continue
        title = _extract_html_text(link_match.group(2))
        url = urljoin(source.feed_url, html.unescape(link_match.group(1)))
        summary_match = _PARAGRAPH_PATTERN.search(block)
        summary = _extract_html_text(summary_match.group(1)) if summary_match else title
        time_match = _TIME_DATETIME_PATTERN.search(block)
        published_at = _parse_datetime(time_match.group(1)) if time_match else None
        if title and _looks_like_content_url(url):
            candidates.append(
                _HtmlCandidate(
                    title=title,
                    url=url,
                    summary=summary,
                    published_at=published_at,
                )
            )
    return candidates


def _extract_link_candidates(
    *,
    source: AiHotTrackerSourceDefinition,
    payload: str,
) -> list[_HtmlCandidate]:
    candidates: list[_HtmlCandidate] = []
    seen_urls: set[str] = set()
    for href, raw_title in _LINK_PATTERN.findall(payload):
        title = _extract_html_text(raw_title)
        url = urljoin(source.feed_url, html.unescape(href))
        if url in seen_urls or not _looks_like_content_url(url) or len(title) < 18:
            continue
        seen_urls.add(url)
        candidates.append(_HtmlCandidate(title=title, url=url, summary=title))
        if len(candidates) >= 12:
            break
    return candidates


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


def _extract_html_text(value: str | None) -> str:
    if not value:
        return ""
    parser = _FeedHtmlTextExtractor()
    parser.feed(value)
    return parser.text()


def _clean_text(value: str | None) -> str:
    if not value:
        return ""

    stripped = html.unescape(_TAG_PATTERN.sub(" ", value))
    normalized = _WHITESPACE_PATTERN.sub(" ", stripped).strip()
    return normalized[:480]


def _build_source_item(
    *,
    source: AiHotTrackerSourceDefinition,
    raw_id: str,
    title: str,
    url: str,
    summary: str,
    published_at: datetime | None,
) -> AiHotTrackerSourceItem:
    return AiHotTrackerSourceItem(
        id=_stable_item_id(source.id, raw_id),
        source_id=source.id,
        source_label=source.label,
        source_kind=source.source_kind,
        category=source.category,
        source_family=source.source_family,
        title=title,
        url=url,
        summary=summary,
        published_at=published_at,
        tags=list(source.tags),
        audience_tags=list(source.audience_tags),
    )


def _looks_like_content_url(url: str) -> bool:
    lowered = url.lower()
    if any(fragment in lowered for fragment in ("#","/tag/","/category/","/author/","/about")):
        return False
    return lowered.startswith("http://") or lowered.startswith("https://")


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
