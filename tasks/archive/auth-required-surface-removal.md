# Task: Remove Retained Auth-Required Surface

## Goal

Remove the retained `需要先登录` card from protected product paths and replace it with a direct login redirect that keeps user flow cleaner.

## Scope

- change the shared auth-required surface so protected pages no longer render the old card
- preserve route intent by sending users to `/login`
- restore post-login continuity by returning users to their original page after login
- update control-plane docs for this durable UX decision

## Verification

- `npm --prefix web run verify`
- `git diff --check`
