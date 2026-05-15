# Fix qwen3.6 report-generation timeout

## Status

- Completed: 2026-05-15

## Context

After switching chat and evaluation calls from `qwen-plus` to `qwen3.6-plus`, the deployed AI hot tracker could reach the provider successfully but still saved the latest run as `degraded` with `report_generation_failed`.

Direct provider probes showed that `qwen3.6-plus` defaults to returning a long `reasoning_content` payload. The simple JSON-mode probe worked, but the default thinking path was much slower than the same request with `enable_thinking=false`. The latest public hot-tracker run took 213 seconds before degrading, which matched two 90-second report-generation attempts plus source work.

## Scope

- Keep `qwen3.6-plus` as the selected model.
- Disable Qwen 3.6 thinking mode in the shared model interface.
- Preserve existing public APIs and hot-tracker product behavior.
- Add a regression test to ensure Qwen 3.6 payloads include `enable_thinking=false`.

## Verification

- `cd server && ..\\.venv\\Scripts\\python.exe -m pytest tests\\test_model_interface_service.py tests\\test_ai_hot_tracker_report_service.py`
- Direct provider probe confirmed JSON mode with `enable_thinking=false` returns `200`.

