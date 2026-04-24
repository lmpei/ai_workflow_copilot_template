# Task: AI Hot Tracker Strong Agent Product

## Goal

Make `AI 热点追踪` behave like one durable strong-agent product for mainstream AI users instead of one report-generation page.

## Product Direction

- Audience: mainstream AI users who want judgment, not a research console.
- Core value: tell the user what happened, why it matters now, who should care, and what to keep watching.
- Product loop: trusted-source sensing -> event memory -> judgment brief -> grounded follow-up -> saved history -> runtime state -> internal evaluation.
- User surface: brief on the left, follow-up on the right, light history drawer, light profile settings.
- Internal model: layered hot-tracker agent roles (`Scout`, `Resolver`, `Analyst`, `Editor`, `Evaluator`, `Follow-up`) without exposing agent internals on the consumer path.

## Scope

- Add durable event memory for AI hot tracker so the system remembers signals beyond the last saved snapshot.
- Extend source definitions and source items with strong-agent fields such as source strategy, parse mode, audience tags, score traces, and event affiliation.
- Extend the hot-tracker brief contract with `confidence` and `blindspots`.
- Persist internal role outputs and event-memory summaries into the run evaluation path.
- Tighten follow-up so it stays grounded in the current run, current sources, current blindspots, and prior follow-up history.
- Rewrite the hot-tracker workspace surface in clean product Chinese and align it with the new brief contract.
- Keep `?view=evaluation` as the internal inspection path for ranking, clustering, change state, source failures, event memory, and brief output.

## Out Of Scope

- No new module work outside `AI 热点追踪`.
- No user-defined sources.
- No generic public crawling.
- No full-article media crawling.
- No external notification center or email/webhook delivery.
- No consumer-facing exposure of internal agent graph terms.

## Verification

- Backend: `cd server` then `..\\.venv\\Scripts\\python.exe -m pytest tests`
- Frontend: `npm --prefix web run verify`
