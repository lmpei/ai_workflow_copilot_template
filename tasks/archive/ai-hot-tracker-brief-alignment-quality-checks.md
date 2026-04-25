# Task: AI Hot Tracker Brief Alignment Quality Checks

## Goal

Push `AI hot tracker` closer to its end-state by making internal evaluation judge whether the saved brief
actually stays aligned with the underlying decision layer.

## Why

The module already has runtime state, replay calibration, and run-level evaluation, but that still leaves one
important blind spot: a saved brief can look polished while drifting away from the actual delta or cluster-level
judgment underneath it.

If we do not check that layer explicitly, the product can still overstate priority, hide the strongest signal,
or merge multiple events into one vague headline without the internal evaluation view calling it out clearly.

## Scope

- Extend run evaluation with deterministic brief-alignment checks.
- Check change-state honesty, high-priority signal coverage, cluster consistency, priority alignment, and change-type alignment.
- Add or update tests that prove both good and bad briefs are surfaced correctly by evaluation.
- Sync `STATUS.md`, `DECISIONS.md`, and `ARCHITECTURE.md` when the slice is durable.

## Out Of Scope

- No new source families.
- No new consumer-facing product surfaces.
- No replay corpus expansion in this slice.
- No deployment or environment changes.

## Verification

- Backend: `cd server` then `..\\.venv\\Scripts\\python.exe -m pytest tests/test_ai_hot_tracker_decision_service.py tests/test_ai_hot_tracker_replay_service.py tests/test_ai_hot_tracker_report_service.py tests/test_ai_hot_tracker_tracking_runs.py tests/test_scenario_contract_service.py`
- Frontend: `npm --prefix web run verify`
