# Switch default Qwen model to qwen3.6-plus

## Status

- Completed: 2026-05-15

## Context

The deployed AI hot tracker was configured to use `qwen-plus` for chat and evaluation calls. The account still had free quota on newer Qwen models, while `qwen-plus` no longer had usable free quota.

## Scope

- Change local and deployment model configuration from `qwen-plus` to `qwen3.6-plus`.
- Keep the existing DashScope OpenAI-compatible base URL.
- Keep `text-embedding-v4` unchanged.
- Verify that `qwen3.6-plus` works for both ordinary chat completions and JSON-mode completions.

## Result

- Runtime `.env.weave` on the server now uses `CHAT_MODEL=qwen3.6-plus` and `EVAL_MODEL=qwen3.6-plus`.
- Local `.env` was updated the same way.
- Repository defaults and environment examples now use `qwen3.6-plus`.
- The public API health check passed.
- Direct provider probes returned `200` for both plain chat and JSON-mode calls.

