#!/usr/bin/env bash

set -euo pipefail

REPO_DIR="${REPO_DIR:-/home/ubuntu/ai_workflow_copilot_template}"
COMPOSE_FILE="${COMPOSE_FILE:-${REPO_DIR}/docker-compose.weave-stack.yml}"
ENV_FILE="${ENV_FILE:-${REPO_DIR}/.env.weave}"

if [[ ! -d "${REPO_DIR}" ]]; then
  echo "Missing repo directory: ${REPO_DIR}" >&2
  exit 1
fi

if [[ ! -f "${COMPOSE_FILE}" ]]; then
  echo "Missing compose file: ${COMPOSE_FILE}" >&2
  exit 1
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing env file: ${ENV_FILE}" >&2
  exit 1
fi

cd "${REPO_DIR}"

echo "==> Deploying weave from commit $(git rev-parse --short HEAD)"
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d --build
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T server python -m alembic upgrade head

echo "==> Local health checks"
curl -fsS http://127.0.0.1:3001 >/dev/null
curl -fsS http://127.0.0.1:8001/api/v1/health >/dev/null

echo "==> Service status"
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps
