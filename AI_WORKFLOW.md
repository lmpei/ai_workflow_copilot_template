# AI Workflow

## AI-Native Development Workflow

This repository follows an AI-native workflow designed for human plus AI collaboration.

## Core Principles

1. spec-driven development
2. agentic execution
3. current-state visibility
4. automated verification
5. human review

## Development Flow

Idea -> Status and Context Alignment -> Decisions -> PRD -> Architecture -> Task Planning -> Agent Implementation -> Verification -> Human Review

## Step 1 - Idea

Define the feature or direction change.

Executed by: Human

## Step 2 - Status and Context Alignment

Locations:

- `STATUS.md`
- `CONTEXT.md`
- `DECISIONS.md`

Purpose:

Make the current objective, stable facts, and already-confirmed decisions explicit before planning implementation.

## Step 3 - PRD

Location:

- `docs/prd/`

Purpose:

Describe the feature, user, and expected outcome.

## Step 4 - Architecture

Locations:

- `ARCHITECTURE.md`
- `docs/architecture/`

Purpose:

Define system boundaries, modules, and data flow.

## Step 5 - Task Planning

Location:

- `tasks/`

Purpose:

Break a feature into small executable tasks with clear scope and verification commands.

## Step 6 - Agent Implementation

Agents execute scoped tasks.

Agents may:

- read files
- edit code
- run commands
- create tests
- update the control-plane docs when the change is durable

## Step 7 - Verification

Run automated validation before handoff.

Typical checks:

- backend tests
- frontend verify
- docs consistency review for docs-only tasks

If verification fails, the agent should keep iterating or clearly document the blocker.

## Step 8 - Human Review

Humans review:

- architecture decisions
- security risks
- edge cases
- sequencing choices
- whether confirmed decisions should be added to `DECISIONS.md`

## Summary

AI-native development workflow:

Status and Context -> Decisions -> Specs -> Tasks -> Agents -> Verification -> Review

Human role:

- direction setter
- reviewer
- decision confirmer

AI role:

- scoped executor
- repository maintainer
- documentation updater for confirmed work
