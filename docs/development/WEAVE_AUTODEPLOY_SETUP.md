# Weave Auto-Deploy Setup

## Goal

Automatically deploy this repository's product stack to the existing weave host after a successful push to `main`.

Current target:

- host: `101.32.216.83`
- user: `ubuntu`
- repo dir: `/home/ubuntu/ai_workflow_copilot_template`
- runtime command:
  - `docker compose -f docker-compose.weave-stack.yml --env-file .env.weave up -d --build`

## Repo-Owned Pieces

- server deploy script:
  - `scripts/deploy-weave.sh`
- server rollback script:
  - `scripts/rollback-weave.sh`
- GitHub Actions workflow:
  - `.github/workflows/deploy-weave.yml`

The workflow is designed to:

1. wait for `CI` to succeed on `main`
2. SSH into the production host
3. run `/home/ubuntu/deploy-weave.sh`
4. write a clear retry and rollback summary if deploy fails
5. write a clear "deploy skipped because CI failed" summary when upstream `CI` blocks deployment

## One-Time Server Setup

Install one stable wrapper on the server:

```bash
cat >/home/ubuntu/deploy-weave.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

cd /home/ubuntu/ai_workflow_copilot_template
git fetch origin main
git checkout main
git pull --ff-only origin main
bash /home/ubuntu/ai_workflow_copilot_template/scripts/deploy-weave.sh
EOF

chmod +x /home/ubuntu/deploy-weave.sh
```

## One-Time GitHub Secret Setup

Add this repository secret:

- `WEAVE_DEPLOY_SSH_KEY`
  - the private key used by GitHub Actions to SSH into `ubuntu@101.32.216.83`

Recommended setup:

1. create one dedicated deploy key pair
2. add the public key to `/home/ubuntu/.ssh/authorized_keys`
3. store the private key in the GitHub repository secret

## Routine Flow

After setup, the normal flow becomes:

1. push to `main`
2. `CI` runs
3. `Deploy Weave` runs automatically after successful `CI`
4. the server pulls, rebuilds, migrates, and verifies local health

If deploy fails, the workflow run summary now includes one copyable retry path and one copyable rollback path.
If deploy does not start because upstream `CI` failed, the `Deploy Weave` run now still records a summary with:

- the blocked branch
- the upstream `CI` conclusion
- a direct link to the failed `CI` run
- the next step: fix `CI`, then push again

## Retry And Rollback

Retry on the current `main` state:

```bash
ssh ubuntu@101.32.216.83
/home/ubuntu/deploy-weave.sh
```

Roll back to one known-good git ref:

```bash
ssh ubuntu@101.32.216.83
cd /home/ubuntu/ai_workflow_copilot_template
bash scripts/rollback-weave.sh <known-good-ref>
```

Example:

```bash
bash scripts/rollback-weave.sh 0489e23
```

After retry or rollback, verify:

```bash
curl -I https://weave.lmpai.online
curl https://api.lmpai.online/api/v1/health
```

## Manual Backstop

If automation must be run manually:

```bash
ssh ubuntu@101.32.216.83
/home/ubuntu/deploy-weave.sh
```
