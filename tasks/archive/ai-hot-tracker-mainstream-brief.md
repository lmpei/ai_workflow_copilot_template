# Task: AI Hot Tracker Mainstream Brief Closure

## Goal

Make `AI 热点追踪` a complete consumer-facing AI signal brief product for mainstream AI users.

## Product Direction

- Audience: mainstream AI users, not researchers or internal operators.
- Core value: help users decide what is worth paying attention to.
- Source boundary: fixed allowlisted trusted sources, with official sources plus a small set of selected media feeds.
- Output: judgment-oriented brief, not a news feed, research report, or technical debug page.
- Product loop: in-product run, read, ask follow-up, save, revisit, delete, and auto-check.

## Scope

- Expand source definitions and parsing for official, media, research, open-source, product, and developer-tool sources.
- Add impact-oriented ranking while keeping novelty, freshness, authority, and relevance.
- Keep clustering conservative while allowing same-event official and media items to merge.
- Add `impact` and `audience` to brief signals.
- Rewrite AI hot tracker generation and follow-up prompts in clear Chinese.
- Update the frontend brief and evaluation surfaces without exposing algorithm terms in the consumer path.
- Add or update backend and frontend tests for the product loop.

## Out Of Scope

- No new module work.
- No user-defined sources.
- No generic web crawling.
- No full article crawling from media sites.
- No external notifications.
- No public technical debug surface.

## Verification

- Backend: `cd server` then `..\\.venv\\Scripts\\python.exe -m pytest tests`
- Frontend: `npm --prefix web run verify`
