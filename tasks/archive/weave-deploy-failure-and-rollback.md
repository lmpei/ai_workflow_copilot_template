# Task: Weave Deploy Failure Guidance And Rollback Path

## Goal

Make weave production deploy failures easier to understand and recover from by adding one explicit rollback path and one
clear failure summary in the auto-deploy workflow.

## Scope

- add one repo-owned rollback script for the weave stack
- add one clear failure-summary step to the GitHub Actions deploy workflow
- document the retry and rollback procedure in the deploy setup doc
- update control-plane docs to treat this failure-handling path as part of the stable deploy baseline

## Non-Goals

- build a full blue-green or canary deploy system
- add automatic rollback without human confirmation
- change the current production host, compose topology, or domain routing

## Acceptance

- the repo contains one rollback script that can redeploy a known-good git ref
- the deploy workflow writes a clear failure summary with retry and rollback instructions
- the deploy setup doc explains retry vs rollback in one place
- control-plane docs reflect that weave deploys now include an explicit failure-handling path
