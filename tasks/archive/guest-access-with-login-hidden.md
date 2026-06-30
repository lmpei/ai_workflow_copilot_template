# Guest access with login hidden

## Goal

Make the public product usable without showing the unfinished account/password entry flow.

## Scope

- Add a backend guest session endpoint.
- Keep bearer-token authorization for protected APIs.
- Allow deployments to hide password login while keeping guest access open.
- Make the homepage create a guest session automatically when guest access is enabled.
- Replace the previously deployed "closed product access" default with explicit guest-mode switches.
- Update control-plane docs and archive this task after verification.

## Non-goals

- Do not remove authentication from protected APIs.
- Do not reopen Support Copilot or Job Assistant.
- Do not add social login, email verification, or a full onboarding flow.

## Result

- Implemented `POST /auth/guest` with guest users and bearer tokens.
- Added `GUEST_ACCESS_ENABLED`, `PASSWORD_AUTH_DISABLED`, `NEXT_PUBLIC_GUEST_ACCESS_ENABLED`, and `NEXT_PUBLIC_PASSWORD_AUTH_DISABLED`.
- Restored `PUBLIC_AUTH_DISABLED` / `NEXT_PUBLIC_AUTH_DISABLED` to emergency hard-close switches instead of deployed defaults.
- Updated the homepage and auth overlay so public guest mode does not show the account/password form.
- Added backend auth regression tests for guest access and password-entry disablement.
