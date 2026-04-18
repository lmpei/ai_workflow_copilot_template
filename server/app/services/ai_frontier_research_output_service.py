from collections import Counter
from typing import Any

from app.connectors.research_external_context_connector import ResearchExternalContextEntry
from app.schemas.ai_frontier_research import (
    AiFrontierEvent,
    AiFrontierProjectCard,
    AiFrontierReferenceSource,
    AiFrontierResearchOutput,
    AiFrontierTheme,
)


def _extract_prefixed_link(snippet: str, prefix: str) -> str | None:
    for line in snippet.splitlines():
        line = line.strip()
        if line.startswith(prefix):
            value = line[len(prefix) :].strip()
            if value:
                return value
    return None


def _normalize_tags(raw_tags: Any) -> list[str]:
    if not isinstance(raw_tags, list):
        return []
    return [value.strip() for value in raw_tags if isinstance(value, str) and value.strip()]


def _build_project_cards_from_tool_items(raw_items: Any) -> list[AiFrontierProjectCard]:
    if not isinstance(raw_items, list):
        return []

    cards: list[AiFrontierProjectCard] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        title = item.get("title")
        source_label = item.get("source_label")
        summary = item.get("summary")
        why_it_matters = item.get("why_it_matters")
        if not all(isinstance(value, str) and value.strip() for value in (title, source_label, summary, why_it_matters)):
            continue
        cards.append(
            AiFrontierProjectCard(
                title=title.strip(),
                source_label=source_label.strip(),
                summary=summary.strip(),
                why_it_matters=why_it_matters.strip(),
                official_url=item.get("source_url") if isinstance(item.get("source_url"), str) else None,
                repo_url=item.get("repo_url") if isinstance(item.get("repo_url"), str) else None,
                docs_url=item.get("docs_url") if isinstance(item.get("docs_url"), str) else None,
                tags=_normalize_tags(item.get("tags")),
            )
        )
    return cards


def _build_project_cards_from_matches(matches: list[ResearchExternalContextEntry]) -> list[AiFrontierProjectCard]:
    cards: list[AiFrontierProjectCard] = []
    for match in matches:
        summary = match.snippet.splitlines()[0].strip() if match.snippet else match.title
        why_it_matters = ""
        for line in match.snippet.splitlines():
            line = line.strip()
            if line.startswith("为什么重要："):
                why_it_matters = line.replace("为什么重要：", "", 1).strip()
                break
        cards.append(
            AiFrontierProjectCard(
                title=match.title,
                source_label=match.source_label,
                summary=summary,
                why_it_matters=why_it_matters or "这条项目或事件值得继续跟进，并结合原始链接做进一步验证。",
                official_url=_extract_prefixed_link(match.snippet, "官网："),
                repo_url=_extract_prefixed_link(match.snippet, "仓库："),
                docs_url=_extract_prefixed_link(match.snippet, "文档："),
                tags=list(match.keywords[:4]),
            )
        )
    return cards


def _build_reference_sources(project_cards: list[AiFrontierProjectCard]) -> list[AiFrontierReferenceSource]:
    seen: set[tuple[str, str]] = set()
    references: list[AiFrontierReferenceSource] = []
    for card in project_cards:
        candidates = [
            ("official", f"{card.title} 官方来源", card.official_url),
            ("repository", f"{card.title} 仓库", card.repo_url),
            ("docs", f"{card.title} 文档", card.docs_url),
        ]
        for source_kind, label, url in candidates:
            if not url:
                continue
            key = (source_kind, url)
            if key in seen:
                continue
            seen.add(key)
            references.append(
                AiFrontierReferenceSource(
                    label=label,
                    url=url,
                    source_kind=source_kind,  # type: ignore[arg-type]
                )
            )
    return references


def _build_themes(
    *,
    analysis_focus: str | None,
    search_query: str | None,
    project_cards: list[AiFrontierProjectCard],
) -> list[AiFrontierTheme]:
    tag_counter = Counter(tag for card in project_cards for tag in card.tags if tag)
    themes: list[AiFrontierTheme] = []
    if analysis_focus:
        themes.append(AiFrontierTheme(label="当前分析焦点", summary=analysis_focus))
    if search_query:
        themes.append(AiFrontierTheme(label="本轮搜索线索", summary=search_query))
    for tag, _ in tag_counter.most_common(3):
        themes.append(AiFrontierTheme(label=tag, summary=f"这一轮来源多次指向“{tag}”相关的 AI 前沿变化，值得持续跟踪。"))
    return themes[:4]


def _build_events(project_cards: list[AiFrontierProjectCard]) -> list[AiFrontierEvent]:
    return [
        AiFrontierEvent(title=card.title, summary=card.summary, significance=card.why_it_matters)
        for card in project_cards[:4]
    ]


def _build_trend_judgment(*, degraded_reason: str | None, project_cards: list[AiFrontierProjectCard]) -> str:
    if degraded_reason:
        return "这轮判断仍可作为工作起点，但外部上下文不完整，后续应优先补齐最新来源再扩大结论。"
    if not project_cards:
        return "这轮结论主要依赖摘要级上下文，适合继续跟踪主题，但还不足以形成更强的项目判断。"
    lead = project_cards[0]
    return f"当前最值得继续跟进的是“{lead.title}”所代表的变化，并结合附带原始链接验证其持续性与采用价值。"


def build_ai_frontier_research_output(
    *,
    answer: str,
    analysis_focus: str | None,
    search_query: str | None,
    degraded_reason: str | None,
    external_matches: list[ResearchExternalContextEntry],
    tool_structured_content: dict[str, Any] | None,
) -> AiFrontierResearchOutput:
    raw_items = tool_structured_content.get("items") if isinstance(tool_structured_content, dict) else None
    project_cards = _build_project_cards_from_tool_items(raw_items) or _build_project_cards_from_matches(external_matches)
    return AiFrontierResearchOutput(
        frontier_summary=answer.strip(),
        trend_judgment=_build_trend_judgment(degraded_reason=degraded_reason, project_cards=project_cards),
        themes=_build_themes(analysis_focus=analysis_focus, search_query=search_query, project_cards=project_cards),
        events=_build_events(project_cards),
        project_cards=project_cards,
        reference_sources=_build_reference_sources(project_cards),
    )
