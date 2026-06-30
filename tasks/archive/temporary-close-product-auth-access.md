# Temporarily close product auth access

## Summary

Temporarily close all login-required product access while keeping the deployment alive. The public homepage can still load, but users cannot log in, create an account implicitly through the unified auth entry, or use existing tokens to access protected product APIs.

## Scope

- Add a backend runtime switch for public auth closure.
- Add a frontend build/runtime switch so the auth overlay shows a closed-access state instead of the account/password form.
- Wire the switch into the weave deployment compose path.
- Update env examples and control-plane docs.
- Verify auth behavior locally and deploy the switch to the public server.

## Acceptance

- `POST /auth/enter`, `POST /auth/login`, and `POST /auth/register` return `403` when the switch is enabled.
- Existing bearer tokens are also rejected by protected routes when the switch is enabled.
- The homepage auth overlay shows a temporary closed-access message when the frontend switch is enabled.
- Production deployment can set the switch without code changes.
