from dataclasses import dataclass
import re


class ResearchExternalContextConnectorUnavailableError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class ResearchExternalContextEntry:
    context_id: str
    title: str
    source_label: str
    keywords: tuple[str, ...]
    snippet: str


_CATALOG: tuple[ResearchExternalContextEntry, ...] = (
    ResearchExternalContextEntry(
        context_id="market-cost-pressure",
        title="Analyst note: margin pressure and price discipline",
        source_label="External market note",
        keywords=("pricing", "margin", "cost", "pressure", "discipline", "competition"),
        snippet=(
            "Recent analyst commentary suggests that price discipline is holding only in premium segments, "
            "while cost pressure is eroding margins in the mid-market."
        ),
    ),
    ResearchExternalContextEntry(
        context_id="policy-shift-demand",
        title="Industry brief: policy shifts affecting demand timing",
        source_label="External industry brief",
        keywords=("policy", "demand", "timing", "regulation", "procurement", "market"),
        snippet=(
            "Policy changes are shifting demand timing rather than removing demand entirely, with procurement "
            "cycles stretching longer in regulated categories."
        ),
    ),
    ResearchExternalContextEntry(
        context_id="customer-signal-adoption",
        title="Field digest: customer adoption signal",
        source_label="External field digest",
        keywords=("customer", "adoption", "trial", "conversion", "signal", "usage"),
        snippet=(
            "Field reports indicate healthy trial interest, but conversion depends heavily on how quickly the "
            "product proves operational value within the first evaluation window."
        ),
    ),
)


def _tokenize(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) >= 3
    }


def search_research_external_context(*, query: str, limit: int = 3) -> list[ResearchExternalContextEntry]:
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    scored: list[tuple[int, ResearchExternalContextEntry]] = []
    for entry in _CATALOG:
        haystack_tokens = query_tokens & (
            set(entry.keywords)
            | _tokenize(entry.title)
            | _tokenize(entry.snippet)
        )
        score = len(haystack_tokens)
        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda item: (-item[0], item[1].title))
    return [entry for _, entry in scored[: max(1, min(limit, 5))]]
