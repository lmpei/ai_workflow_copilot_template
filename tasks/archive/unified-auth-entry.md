# Unified Auth Entry

## Goal

Collapse the frontend auth experience into one surface with one submission path:

- the UI shows only `账号` and `密码`
- submit first tries account entry
- if the account does not exist, create it and sign in
- if the account exists, sign in
- if the password is wrong, return an auth error

## Scope

- add one backend auth entry endpoint
- keep legacy `/auth/login` and `/auth/register` for compatibility
- replace the current login/register frontend split with one page
- redirect `/register` to the unified auth page
- update tests and control-plane docs

## Verification

- `cd server && ..\\.venv\\Scripts\\python.exe -m pytest tests`
- `npm --prefix web run verify`
- `git diff --check`
