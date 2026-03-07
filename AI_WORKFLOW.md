# AI Workflow

## AI-Native Development Workflow

This repository follows an AI-native workflow designed for human + AI agent collaboration.

## Core Principles

1. Spec-driven development
2. Agentic execution
3. AI-friendly repository design
4. Automated verification
5. Human review

## Development Flow

Idea -> PRD -> Architecture -> Task Planning -> Agent Implementation -> Verification -> Human Review -> Pull Request

## Step 1 - Idea

Define the feature goal.

Example:

Add RAG chat for uploaded documents.

Executed by: Human

## Step 2 - PRD

Location:

`docs/prd/`

Purpose:

Describe the feature, user, and expected outcome.

## Step 3 - Architecture

Location:

`docs/architecture/`

Purpose:

Define system modules and data flow.

Example pipeline:

Document -> Chunk -> Embedding -> Vector DB -> Retrieval -> LLM

## Step 4 - Task Planning

Location:

`tasks/`

Purpose:

Break a feature into small executable tasks with clear scope and verification commands.

Example:

- `TASK-001` document upload API
- `TASK-002` document chunking
- `TASK-003` embedding pipeline
- `TASK-004` vector search
- `TASK-005` chat endpoint

## Step 5 - Agent Implementation

AI coding agents execute scoped tasks.

Agents may:

- read files
- edit code
- run commands
- create tests

Typical tools:

- filesystem
- git
- pytest
- docker

When documenting local commands, match the active shell. For Windows PowerShell, prefer `Copy-Item`,
`python -m <tool>`, and `npm.cmd` where needed.

## Step 6 - Verification

Run automated validation before handoff.

Typical commands:

- `pytest`
- `lint`
- `type check`
- `build`

If verification fails, the agent should keep iterating until the task passes or clearly document the blocker.

## Step 7 - Human Review

Humans review:

- architecture decisions
- security risks
- edge cases
- performance implications

## Step 8 - Pull Request

Final result is submitted as a PR including:

- code
- tests
- documentation

CI runs validation pipelines automatically.

## Summary

AI-native development workflow:

Spec -> Tasks -> Agents -> Verification -> Review -> PR

Human role:

Architect + reviewer

AI role:

Task executor
