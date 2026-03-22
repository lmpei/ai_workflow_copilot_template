# Global Governance Baseline Initiated During Stage C Early Execution

## Purpose

This document records the global governance baseline identified during Stage C early execution and turns it into a
durable cleanup reference. It is not a feature PRD and it is not only a Stage C module-depth artifact. It is the
architectural and maintainability baseline that should guide the rest of Stage C execution and the planning unit that
follows.

## Status

- Status: active global reference
- Created At: 2026-03-22
- Positioning: global governance baseline initiated during Stage C early execution
- Source: static repository diagnosis plus focused subagent analysis

## Why This Exists

Stage C broadened the platform beyond the Research reference flow, and that early execution exposed structural drift in
the shared core. The main risk is not isolated code style debt. The main risk is that the repository now has duplicated
contracts, eroded boundaries, and hidden JSON-based coupling that can turn every new module increment into
multi-surface rework. This baseline is global because the problems cut across backend, frontend, runtime, and docs,
even though they were formalized after Stage C had already started.

## Review Scope

The diagnosis focused on:

- duplicated abstractions
- terminology inconsistency
- module boundary erosion
- layer leakage
- mixed levels of abstraction
- implicit coupling
- misleading naming
- unstable abstractions
- hidden dependencies
- folder structure that does not match the real architecture

## Structural Findings

### 1. Duplicated module identity and terminology

- Severity: high
- Must be fixed before next stage: yes
- Typical files:
  - `server/app/models/workspace.py`
  - `server/app/schemas/workspace.py`
  - `server/app/schemas/scenario.py`
  - `web/lib/types.ts`
- Diagnosis:
  - module identity is split across `type` and `module_type`
  - task selectors drift across `task_type` and `scenario_task_type`
  - lifecycle language drifts across `done` and `completed`
  - scenario inputs drift across `goal`, `question`, `customer_issue`, and `target_role`

### 2. Repeated registry and switchboard logic

- Severity: high
- Must be fixed before next stage: yes
- Typical files:
  - `server/app/schemas/scenario.py`
  - `server/app/services/task_service.py`
  - `server/app/services/task_execution_service.py`
  - `web/lib/navigation.ts`
  - `web/components/evals/eval-manager.tsx`
- Diagnosis:
  - module labels, entry task types, eval labels, and scenario groupings are repeated across backend and frontend
  - shared services dispatch by hard-coded scenario lists instead of consuming one canonical registry

### 3. Raw JSON is acting as the real cross-layer contract

- Severity: high
- Must be fixed before next stage: yes
- Typical files:
  - `server/app/schemas/task.py`
  - `server/app/services/research_asset_service.py`
  - `web/components/research/research-assistant-panel.tsx`
  - `web/components/support/support-copilot-panel.tsx`
  - `web/components/job/job-assistant-panel.tsx`
- Diagnosis:
  - panels and services inspect `output_json`, `result`, and `module_config_json` directly
  - the repository behaves as if storage shape and API shape are the same contract

### 4. Layer boundaries are no longer trustworthy

- Severity: high
- Must be fixed before next stage: yes
- Typical files:
  - `server/app/repositories/workspace_repository.py`
  - `server/app/services/scenario_contract_service.py`
  - `server/app/agents/tool_registry.py`
- Diagnosis:
  - repository code depends on service-layer contract resolution
  - runtime tooling touches repository details directly
  - visible `routes -> services -> repositories` layering no longer matches the real call graph

### 5. Scenario boundaries rely on compatibility guesses

- Severity: high
- Must be fixed before next stage: yes
- Typical files:
  - `server/app/services/support_copilot_service.py`
  - `server/app/services/job_assistant_service.py`
  - `server/app/services/scenario_eval_service.py`
- Diagnosis:
  - Support and Job still accept Research-style `goal` fallback input
  - eval prompt assembly guesses which scenario field should be treated as the main prompt

### 6. Shared execution has become Research-biased

- Severity: high
- Must be fixed before next stage: partially
- Typical files:
  - `server/app/services/task_execution_service.py`
  - `server/app/services/research_assistant_service.py`
  - `server/app/services/research_asset_service.py`
  - `server/app/agents/graph.py`
- Diagnosis:
  - the shared executor mixes queueing, tracing, lineage, asset sync, and scenario dispatch
  - several concerns inside the shared path are effectively Research-only
  - scenario graphs are near-duplicate pipelines without an explicit shared skeleton

### 7. Runtime-control semantics are duplicated

- Severity: high
- Must be fixed before next stage: yes
- Typical files:
  - `server/app/core/runtime_control.py`
  - `server/app/services/task_service.py`
  - `server/app/services/eval_service.py`
  - `server/app/services/task_execution_service.py`
  - `server/app/services/eval_execution_service.py`
- Diagnosis:
  - task and eval control paths both implement cancel and retry orchestration
  - the recovery model exists conceptually, but the execution logic is still duplicated

### 8. Folder naming and visible structure mislead contributors

- Severity: medium
- Must be fixed before next stage: no, but should be cleaned early
- Typical files:
  - `web/components/tasks/task-manager.tsx`
  - `web/components/tasks/task-module-panel.tsx`
  - `web/lib/navigation.ts`
  - `server/app/api/routes/agents.py`
  - `server/app/workers/report_worker.py`
  - `server/app/workers/classification_worker.py`
  - `server/app/workers/ingest_worker.py`
- Diagnosis:
  - several names still reflect older surfaces or placeholder scaffolds
  - current folder layout implies cleaner boundaries than the code actually has

## Cleanup Principles

The governance cleanup should follow these rules:

1. establish one canonical module registry and derive other views from it
2. separate storage shape from API shape and UI view shape
3. keep scenario contracts strict at module boundaries instead of normalizing cross-scenario guesses
4. restore one-way dependency flow from route to service to repository
5. treat Research-specific workflow depth as an extension, not as the implicit default for the shared executor
6. reduce duplicated control semantics and pipeline skeletons before adding more scenario depth

## Required Workstreams Before The Next Planning Unit

### Workstream A. Canonical contracts and terminology

- unify module identity and task-state vocabulary
- define canonical scenario input and output shapes
- stop exposing storage-oriented JSON blobs as frontend contracts

### Workstream B. Registry and boundary hardening

- create one scenario registry for backend and frontend consumption
- remove repository-to-service inversions
- remove cross-scenario fallback input guesses

### Workstream C. Shared execution alignment

- extract a shared scenario execution skeleton from duplicated graph pipelines
- move Research-only concerns behind explicit extension points
- converge task and eval runtime-control orchestration

### Workstream D. Maintainability and surface hygiene

- document runtime-control semantics
- document scenario contract precedence
- mark scaffold and placeholder surfaces honestly
- clean misleading names where the payoff is immediate

## Annotation Priorities

The highest-value maintainability notes identified by the review are:

1. `server/app/core/runtime_control.py`
   - explain cancel and retry state transitions, history normalization, and requested versus applied timestamps
2. `server/app/services/task_execution_service.py`
   - label the shared execution path versus Research-only extension points
3. Research result contract docs
   - define the stable result shape consumed by assets and UI panels
4. scenario input precedence docs
   - define canonical scenario fields so task creation, evals, and UI stop guessing
5. scaffold surface notes
   - mark placeholder workers and generic-looking agent routes that are not yet real product surfaces

## Global Governance Baseline Workstreams

This global governance baseline is currently executed through the following Stage C task identifiers:

- `tasks/stage-c-06-canonical-module-contracts-and-terminology.md`
- `tasks/stage-c-07-scenario-registry-and-boundary-hardening.md`
- `tasks/stage-c-08-runtime-architecture-alignment.md`
- `tasks/stage-c-09-maintainability-annotations-and-surface-hygiene.md`

The planning task that initiated this baseline during Stage C early execution is archived as:

- `tasks/archive/stage-c/stage-c-05-governance-convergence-planning.md`

## Readiness Gate For The Next Planning Unit

The project should not open the next planning unit until the following are true:

- one canonical module identity exists across backend and frontend
- scenario task and result contracts are explicit and typed
- raw JSON payloads are no longer the real UI and service integration contract
- repository and runtime dependency direction is repaired
- task and eval recovery behavior are aligned through shared runtime-control semantics
- the governance cleanup has been reflected in docs, not only in implementation

## Verification

- manual architecture and document consistency review

## Non-Goals

This diagnosis does not itself:

- rename the three module products
- open a new planning unit after Stage C
- replace the existing Stage C feature tasks
- claim that every naming inconsistency must be fixed before any other code can move
