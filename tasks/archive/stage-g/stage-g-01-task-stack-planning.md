# Stage G Task Stack Planning

## Stage Name

`Stage G: Multi-Subdomain Product Split and Shared Edge Routing`

## Planning Decision

After Stage F, the repo no longer needs more front-end shape iteration as its primary concern. The next bounded unit is
to separate the personal site boundary from the product boundary and prepare this repository for deployment as the
dedicated `weave.lmpai.online` product plus `api.lmpai.online` backend behind one shared Cloudflare -> Caddy edge.

## Task Stack

1. `tasks/stage-g-02-weave-subdomain-product-split.md`

## Notes

- The root marketing site at `lmpai.online` is now treated as a separate deployment outside this repository.
- This repository should adapt to the dedicated product host and API host without pretending to own the root personal
  homepage anymore.
