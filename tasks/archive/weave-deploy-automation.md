# Task: Weave Deploy Automation

## Goal

Automate production deploys for the weave product stack on the existing shared server.

## Scope

- add one repo-owned deploy script for the weave stack
- add one GitHub Actions workflow that runs after successful `CI` on `main`
- document the remaining one-time setup clearly
- avoid changing the separate `lmpai.online` homepage deployment path

## Non-Goals

- redesign the server topology
- migrate the homepage service into this repo
- introduce a second production host

## Acceptance

- the repo contains a stable deploy script for weave
- the repo contains an auto-deploy workflow
- the workflow only needs one repository secret for SSH private key material
- docs describe the server wrapper and setup path
