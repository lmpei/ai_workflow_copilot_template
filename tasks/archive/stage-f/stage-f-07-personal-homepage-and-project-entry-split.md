# Task: stage-f-07-personal-homepage-and-project-entry-split

## Goal

Split the root site into a non-logged-in personal homepage and move the current product entry into a dedicated
project-facing route.

## Project Stage

- Stage: Stage F
- Track: Delivery and Operations with Research and Platform Reliability support

## Why

The human clarified that the root home page should introduce the person and the portfolio, not act like the logged-in
entry surface for a single product. As long as the root page and the product entry page share the same job, the site
will keep feeling repetitive and confusing.

## Context

Relevant documents:

- `docs/prd/STAGE_F_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `STATUS.md`
- `CONTEXT.md`

## Scope

Allowed work:

- redesign `/` as a non-logged-in personal homepage
- introduce one durable project-entry route inside the current app for this product
- make the root page link clearly into this project instead of doubling as its workspace center

Disallowed work:

- changing deployment, DNS, or subdomain routing in this task
- reshaping the inside of the project-facing workspace center
- reshaping the inside of an individual workspace

## Acceptance Criteria

- the root page no longer behaves like the product workspace center
- a visitor can understand the person and the project list without logging in
- the current product has one clear project-facing entry route that later can map to a dedicated subdomain without
  changing the product model again
