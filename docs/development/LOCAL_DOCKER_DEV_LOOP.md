# Local Docker Dev Loop

This repo's default `docker-compose.yml` is a local development stack, not a production image-only stack.

## Intended Workflow

1. Start the stack once:
   - `docker compose up server worker web`
2. Keep the stack running while you edit code.
3. Refresh the browser, or wait for frontend hot reload.

Routine code edits in `server/` and `web/` should not require manual rebuilds.

## Why Polling Is Enabled

Windows plus Docker bind mounts can miss filesystem change events. The local stack therefore uses polling-based file
watching for the backend and frontend dev servers so code edits are detected more reliably.

## When You Still Need To Rebuild

Rebuild only when you change image-level inputs, for example:

- `server/requirements.txt`
- `web/package.json`
- `web/package-lock.json`
- any Dockerfile
- any system dependency baked into the image

In those cases, run:

- `docker compose up --build server worker web`

## Notes

- The backend service uses `uvicorn --reload` with polling enabled.
- The frontend service uses `next dev` with polling enabled.
- The frontend service now keeps `.next/` inside a dedicated Docker volume instead of the bind-mounted workspace.
  This avoids stale chunk mismatches between local builds and the long-running dev server.
- The worker still runs as a normal long-lived process; if you change worker-only code paths and do not see the effect,
  restart the `worker` service.

## One-Time Recreate After This Change

Because the `web` service now has a dedicated `.next` volume and a startup cleanup command, recreate it once:

- `docker compose up -d --force-recreate web`

You do not need `--build` for this change unless you also modified image-level dependencies.
