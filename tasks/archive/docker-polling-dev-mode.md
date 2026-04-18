# Docker Polling Dev Mode

## Goal

Make the default local Docker development flow stable on Windows by switching the web and server services to polling-based
file watching, so routine code edits do not require repeated manual rebuilds.

## Scope

- update the local `docker-compose.yml` dev services so frontend and backend file watching uses polling
- preserve the existing one-time `docker compose up` development flow
- document the intended workflow so rebuilds are reserved for dependency or image changes

## Non-Goals

- redesign production deployment compose files
- add full hot reload for the background worker
- change application runtime behavior outside local development

## Verification

- `docker compose config`
- `git diff --check`
