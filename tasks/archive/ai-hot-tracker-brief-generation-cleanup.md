# Task: AI Hot Tracker Brief Generation and Schema Cleanup

## Goal

Clean the AI hot-tracker brief generation path so the module no longer leaks damaged prompt text,
fallback copy, or corrupted schema defaults into the user-facing report flow.

## Why

The ranking, clustering, delta, and runtime-hardening work is only useful if the final brief-generation
contract is clean. Damaged Chinese prompt text inside the brief service or schema defaults directly harms
report quality and can surface broken copy in degraded or fallback paths.

## Scope

- Rewrite the hot-tracker brief generation service onto one clean Chinese prompt and fallback contract.
- Normalize hot-tracker schema defaults and legacy brief fallbacks onto clean UTF-8 Chinese copy.
- Verify that report generation, run persistence, and the frontend build remain stable.

## Out Of Scope

- No new source families.
- No changes to scheduling policy.
- No new UI features.
- No new module work outside `AI ÈÈµã×·×Ù`.

## Verification

- Backend: `cd server` then `..\\.venv\\Scripts\\python.exe -m pytest tests/test_ai_hot_tracker_report_service.py tests/test_ai_hot_tracker_tracking_runs.py tests/test_scenario_contract_service.py`
- Frontend: `npm --prefix web run verify`
