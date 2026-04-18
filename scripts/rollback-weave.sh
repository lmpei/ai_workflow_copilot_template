#!/usr/bin/env bash

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: bash scripts/rollback-weave.sh <git-ref>" >&2
  exit 1
fi

TARGET_REF="$1"
REPO_DIR="${REPO_DIR:-/home/ubuntu/ai_workflow_copilot_template}"
DEPLOY_SCRIPT="${DEPLOY_SCRIPT:-${REPO_DIR}/scripts/deploy-weave.sh}"

if [[ ! -d "${REPO_DIR}" ]]; then
  echo "Missing repo directory: ${REPO_DIR}" >&2
  exit 1
fi

if [[ ! -f "${DEPLOY_SCRIPT}" ]]; then
  echo "Missing deploy script: ${DEPLOY_SCRIPT}" >&2
  exit 1
fi

cd "${REPO_DIR}"

git fetch origin main --tags

if ! git rev-parse --verify --quiet "${TARGET_REF}^{commit}" >/dev/null; then
  echo "Unknown git ref: ${TARGET_REF}" >&2
  exit 1
fi

git checkout "${TARGET_REF}"
echo "==> Rolling weave back to $(git rev-parse --short HEAD)"
bash "${DEPLOY_SCRIPT}"
