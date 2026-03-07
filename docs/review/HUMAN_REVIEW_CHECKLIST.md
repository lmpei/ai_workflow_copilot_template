# Human Review Checklist

Use this checklist before merging agent-authored changes.

## Product and Scope

- Is the change consistent with the PRD and task scope?
- Are out-of-scope changes avoided?

## Architecture

- Does the implementation match the architecture spec?
- Are new abstractions justified and reusable?

## Quality

- Were the required verification commands run?
- Are tests meaningful for the changed behavior?
- Are failure cases and edge cases covered?

## Security and Reliability

- Are inputs validated?
- Are secrets and environment settings handled safely?
- Are retries, idempotency, or error states considered where needed?

## AI-Specific

- Are prompts, tools, or retrieval changes observable and debuggable?
- Are hallucination, source attribution, and fallback behavior considered?
- Are cost and latency implications acceptable for this iteration?

## Documentation

- Are PRD, architecture, task, or README updates needed?
- Is the PR description complete enough for async review?
