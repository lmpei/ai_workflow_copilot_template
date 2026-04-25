# AI 热点追踪终局定义

## Status

This document is the long-term source of truth for the `AI 热点追踪` module.

Use this file when deciding:

- what the product is
- what the internal agent loop is
- which contracts are stable
- what counts as "finished enough" before the project shifts focus

Do not use chat history, archived tasks, or the older frontier-research contract as the primary definition once this file exists.

## Background

`AI 热点追踪` exists to replace the older generic Research story with one narrower and more honest product:

- not a generic research workbench
- not a raw news feed
- not a paper-only assistant
- not a link dump

It is a judgment product for mainstream AI users who want help deciding what matters in the current AI cycle without living inside raw feeds, release notes, and scattered commentary all day.

The product should answer four questions every time a user opens it:

1. 这轮到底发生了什么
2. 为什么它现在重要
3. 这更适合谁关注
4. 接下来还要继续看什么

## Product Definition

### Users

- Primary users:
  - mainstream AI users
  - product builders
  - developers
  - learners trying to keep up with fast-moving AI change
- The module is not designed as a research console for specialists or an operator-facing debug surface.

### User Value

`AI 热点追踪` should help users:

- notice meaningful AI change quickly
- understand why that change matters
- keep a durable memory of prior judgments
- continue asking bounded questions without falling back to generic chat

### Main Product Surface

The consumer-facing surface stays simple:

- left side:
  - one judgment-style brief
- right side:
  - one run-bound follow-up panel
- supporting surfaces:
  - one lightweight history drawer
  - one lightweight tracking-profile editor
  - one runtime summary strip

The ordinary user path must not expose internal technical terms such as:

- `ranking`
- `clustering`
- `delta`
- `RAG`
- `agent trace`

### Default Behavior

- A user can enter the module without prior configuration.
- The workspace starts with one default `tracking_profile`.
- Users may manually request a run at any time.
- The backend may also evaluate the profile on a schedule without requiring the user to stay online.

### Saving and Runtime Behavior

- Manual runs always save one `tracking_run`.
- Automatic runs save only when the state is:
  - `first_run`
  - `meaningful_update`
  - `degraded`
  - `failed`
- Automatic `steady_state` scans update durable tracking state without polluting saved history.

### Follow-up Boundary

The right-side `追问` surface is not open chat.

It must answer only from:

- the selected run's brief
- the selected run's source items
- the selected run's event memory
- the selected run's blindspots
- the selected run's prior follow-ups

When evidence is weak or missing, the module should narrow the answer and say what is not supported by the current run.

### Failure and Honesty

The product should fail honestly:

- source failures should stay visible in evaluation
- degraded judgment should say what is missing
- low-evidence follow-up should narrow instead of bluff
- consumer copy should remain readable Chinese and must not leak broken fallback strings

## Internal Strong-Agent Definition

`AI 热点追踪` is a product on the outside and a bounded strong-agent loop on the inside.

It should behave like one coordinated system with distinct internal roles:

### `Scout`

- reads the fixed allowlist of trusted sources
- ingests only list-level metadata where required
- collects title, summary, time, link, source metadata, and category context
- does not reopen generic crawling or arbitrary user-provided web search

### `Resolver`

- normalizes raw source material into stable `source_item` records
- deduplicates obvious duplicates
- applies conservative same-event clustering
- avoids aggressive merging when evidence is weak

### `Analyst`

- scores candidates using fixed, inspectable judgment logic
- weighs authority, freshness, novelty, relevance, and practical impact
- compares against durable event memory
- decides whether the current state is:
  - `first_run`
  - `meaningful_update`
  - `steady_state`
  - `degraded`
  - `failed`

### `Editor`

- synthesizes the user-facing brief
- keeps the brief aligned with the underlying clustered judgment
- writes in product-facing Chinese instead of research-field dump style

### `Evaluator`

- checks whether ranking, clustering, delta, and saved brief remain aligned
- exposes machine-readable judgment checks on the internal evaluation path
- keeps replay calibration visible without exposing it on the consumer path

### `Follow-up`

- answers bounded questions against the current run
- persists grounding metadata with each answer
- stays within run-bound reasoning instead of drifting into generic assistant behavior

These roles may appear in internal evaluation and inspection. They are not part of the consumer-facing story.

## Core Contracts and Interfaces

### Source Boundary

The module uses a fixed trusted-source allowlist.

Source families include:

- official labs
- official product update surfaces
- developer tooling feeds
- research feeds
- open-source release feeds
- selected media feeds

Media sources are supplementary only and stay at list level. They do not justify full-article crawling as the default path.

### Stable Data Objects

#### `tracking_profile`

Long-lived strategy for one workspace, including:

- enabled categories
- cadence
- alert threshold
- source-selection strategy

#### `source_definition`

Stable source metadata, including:

- `source_family`
- `category`
- `authority_weight`
- `audience_tags`
- `parse_mode`

#### `source_item`

Normalized intake record, including:

- title
- summary
- published time
- canonical link
- source label
- category or tags
- audience tags
- decision-layer scoring fields
- cluster or event linkage

#### `signal_memory`

Durable event-memory layer, including:

- event fingerprint
- first seen and last seen timestamps
- streak count
- continuity or cooling state
- replacement linkage
- latest priority evidence

#### `tracking_run`

The durable saved user-visible run, including:

- profile snapshot
- brief output
- normalized source payload
- cluster-level delta summary
- follow-up history

#### `tracking_state`

The automatic-run memory layer, including:

- last checked time
- last successful scan time
- next due time
- last cluster snapshot
- latest saved-brief timestamp
- latest meaningful-update timestamp
- failure memory

#### `follow_up_thread`

Bounded answer history for the selected run, including persisted grounding metadata.

### Final Brief Contract

The brief contract is stable and product-facing.

Top-level fields:

- `headline`
- `summary`
- `change_state`
- `signals`
- `keep_watching`
- `blindspots`
- `reference_sources`

Each `signal` must carry:

- `title`
- `summary`
- `why_now`
- `impact`
- `audience`
- `change_type`
- `priority_level`
- `confidence`
- `source_item_ids`

### Public Paths

The module should keep one canonical public path family:

- create run
- get state
- list runs
- get one run
- delete run
- create follow-up
- update profile
- read run evaluation
- read replay evaluation

No second public product path should be introduced for the same module.

## Evaluation and Completion Line

### Internal Evaluation

The internal evaluation surface exists behind the bounded evaluation path and should expose:

- `quality_checks`
- `judgment_findings`
- `brief_alignment_checks`
- `follow_up_grounding_checks`
- replay calibration results

Evaluation exists so contributors can inspect:

- why an item ranked high
- why items were merged or kept separate
- why a run was treated as meaningful or steady-state
- whether the saved brief stayed honest to the underlying decision layer
- whether follow-up answers stayed grounded to the selected run

### Completion Line

`AI 热点追踪` counts as finished enough for the project to shift focus only when all of the following remain true:

- automatic evaluation is stable and state transitions are explainable
- replay and run-level evaluation can explain ranking, clustering, delta, and event-memory behavior
- the saved brief remains aligned with underlying judgment
- follow-up remains run-bound and grounded
- the consumer-facing product path does not leak technical shell language
- the module no longer depends on old generic Research definitions to explain itself

Once that line is met, further work is judgment tuning, not foundational redefinition.

## Non-Goals

`AI 热点追踪` does not do the following by default:

- generic web crawling
- user-defined arbitrary source ingestion
- full-article crawling as the main path
- generic open-domain chat
- consumer-facing debug consoles
- exposing ranking, clustering, delta, replay, or internal role traces as the ordinary product story
- shifting primary implementation effort to another module before this definition is satisfied

## Relationship to Older Docs

- `docs/prd/AI_FRONTIER_RESEARCH_CONTRACT.md`
  - historical pointer only
- `STATUS.md`
  - current execution state and next bounded work
- `ARCHITECTURE.md`
  - stable architecture boundaries
- `DECISIONS.md`
  - append-only confirmed choices

If any later task, archived task, or chat summary conflicts with this file, this file wins for the product definition of `AI 热点追踪`.
