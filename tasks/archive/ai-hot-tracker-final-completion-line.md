# Task: AI Hot Tracker Final Completion Line

## Goal

收住 `AI 热点追踪` 的最后一轮稳定化工作，让它达到可停下的终局基线：判断可解释、追问稳定 grounded、运行态诚实可读、热点主链只保留一条 canonical path。

## Project Phase

- Phase: Phase 5 baseline complete
- Scenario module: AI hot tracker

## Why

热点模块的主骨架已经完整，但仓库仍停在未提交的中间态：存在坏编码中文、半收口的 follow-up 提示词、replay 说明字符串损坏，以及一批尚未正式封口的控制面更新。

如果不先把这轮稳定化收口做完，就会继续出现“功能大体可跑，但仓库状态看起来始终不稳”的问题。

## Context

当前热点模块已经有：

- allowlist source intake
- ranking / clustering / delta
- tracking state
- signal memory
- brief synthesis
- grounded follow-up
- internal evaluation
- replay calibration

剩余缺口集中在：

- UTF-8 中文合同清理
- follow-up canonical path 收紧
- replay finding 与案例说明清理
- brief / runtime / evaluation 文案一致性
- 一次完整后端与前端验收后的正式提交

## Flow Alignment

- AI hot tracker:
  - source intake -> decision -> report -> tracking state -> follow-up -> evaluation
- Related APIs:
  - `POST /workspaces/{workspace_id}/ai-hot-tracker/runs`
  - `GET /workspaces/{workspace_id}/ai-hot-tracker/state`
  - `GET /ai-hot-tracker/runs/{run_id}/evaluation`
  - `GET /ai-hot-tracker/replay-evaluation`
  - `POST /ai-hot-tracker/runs/{run_id}/follow-up`

## Scope

Allowed files:

- `server/app/services/ai_hot_tracker_follow_up_service.py`
- `server/app/services/ai_hot_tracker_replay_service.py`
- `server/app/services/ai_hot_tracker_tracking_service.py`
- `server/app/schemas/ai_frontier_research.py`
- `server/tests/test_ai_hot_tracker_*`
- `web/components/research/ai-hot-tracker-workspace.tsx`
- `web/lib/types.ts`
- root control-plane docs
- task archive docs

Disallowed files:

- deployment or environment files
- second-module implementation paths
- new public APIs

## Deliverables

- Code changes:
  - clean remaining hot-tracker mojibake and broken Chinese strings
  - harden follow-up grounding copy and prompt chain
  - normalize replay case descriptions and finding summaries
  - keep evaluation fields aligned with the final canonical output
- Test changes:
  - replay calibration assertions stay readable and deterministic
  - follow-up grounding and evaluation checks remain stable
- Docs changes:
  - sync `STATUS.md`, `ARCHITECTURE.md`, and `DECISIONS.md`
  - archive this completion-line task after the slice is durable

## Acceptance Criteria

- 热点主链不再泄漏损坏中文或半修复提示词
- follow-up 保持 run-bound reasoning，越界时会明确收窄
- replay evaluation 可读、可解释、无乱码
- brief alignment 与 follow-up grounding 字段完整可读
- 后端热点重点回归通过
- 后端全量 `pytest tests` 通过
- 前端 `npm --prefix web run verify` 通过
- 本轮改动形成一次正式提交，不再留未提交中间态

## Verification Commands

- Backend:
  - `cd server`
  - `..\\.venv\\Scripts\\python.exe -m pytest tests`
- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case
  - manual run creates one aligned brief and stable runtime state
- Edge case
  - steady-state replay and continuing signal memory stay suppressed from noisy history
- Error case
  - low-evidence or out-of-scope follow-up returns a bounded answer instead of drifting

## Risks

- broad UTF-8 cleanup in shared schema files can accidentally touch old compatibility behavior
- replay wording cleanup must not change replay semantics or case ids

## Rollback Plan

- revert the hot-tracker-specific service, schema, and frontend changes in one commit
- keep the current run/state persistence model unchanged
