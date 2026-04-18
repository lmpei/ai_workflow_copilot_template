# Task: AI Hot Tracker Report Generation Stability

## Goal

Make the normal `AI 热点追踪` structured report path more stable without introducing a separate fallback-report mode.

## Why

When trusted source intake succeeds, the product should still try hard to complete the normal structured report path. The right fix is to improve generation and schema repair inside that path, not to maintain a second report-building mode.

## Scope

- `server/app/services/ai_hot_tracker_report_service.py`
- `server/tests/test_ai_hot_tracker_report_service.py`
- control-plane status update only

## Deliverables

- one stricter normal-path generation prompt
- one repair attempt when the first structured draft fails validation
- one explicit degraded response only after the normal path still fails
- backend tests covering direct success, repair success, and true failure

## Verification

- `cd server`
- `..\\.venv\\Scripts\\python.exe -m pytest tests`

## Outcome

- completed on 2026-04-17
