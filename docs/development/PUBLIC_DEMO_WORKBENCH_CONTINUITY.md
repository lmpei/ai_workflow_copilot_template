# Public Demo Workbench Continuity

## Purpose

This document defines the bounded continuity contract for the live public demo after Stage E added the first persistent
Support case and Job hiring-packet workbench layers.

It exists to keep the public demo honest. The system now preserves more useful state than a one-off task demo, but it
still does not promise hidden cleanup or production-grade lifecycle management.

## One Bounded Continuity Story

The live public demo now has one simple continuity rule:

1. state inside a workspace is allowed to accumulate
2. a fresh demo path should come from a fresh guided demo workspace
3. true cleanup or hard reset remains an operator decision outside the page flow

In other words, Stage E does not pretend that Support cases or Job hiring packets are disposable page-local widgets.
They are durable workbench objects inside the current workspace until an operator deliberately replaces that workspace or
resets the environment.

## What Persists In The Current Workspace

For the bounded public-demo baseline, the following state may remain visible inside an existing workspace:

- uploaded and seeded documents
- task history
- Research assets and revisions
- Support cases and Support case events
- Job hiring packets and Job hiring-packet events

Normal restart, deploy, or bounded refresh paths should assume that this state can still be present if the underlying
persistent volumes remain intact.

## What Counts As A Clean Demo Path

When an operator wants a clean story for a new viewer, the preferred path is:

1. use a reserved demo account with available workspace slots, or a fresh account if registration is enabled
2. create a new guided demo workspace from the public-demo template catalog
3. walk the new viewer through that new workspace instead of reusing an older workspace with accumulated workbench state

This is the bounded Stage E continuity rule. The live demo should no longer depend on hidden manual cleanup of Support
cases or Job hiring packets between viewers.

## Viewer Start Rule

The public demo now has two honest entry paths:

1. first-time or clean walkthrough
   - create a fresh guided demo workspace
   - follow `Documents -> Chat -> Tasks`
2. existing workbench continuity
   - continue Support work from the visible Support case workbench
   - continue Job work from the visible Job hiring-packet workbench

The demo should not imply a third hidden path where the page silently clears old workbench state before a viewer starts.

## What Does Not Count As An Honest Promise

The live public demo still does not promise:

- silent in-place cleanup of old Support case history
- silent in-place cleanup of old Job hiring-packet history
- automatic per-object reset from the page UI
- permanent retention guarantees for public-demo workspaces
- production-grade data lifecycle controls

If a truly clean slate is required, the operator must create a new guided demo workspace or perform a deliberate
environment reset outside this repo's bounded page flow.

## Stage E Smoke Extension

The minimum public-demo smoke from Stage D still applies. Stage E adds one continuity-specific smoke layer whenever the
operator wants to prove that the new workbench surfaces remain usable.

### Support continuity smoke

- create or open a guided Support demo workspace
- run one Support task if the workspace has no existing case yet
- confirm at least one Support case appears in the workbench
- confirm the latest case event links back to the new task
- confirm the next follow-up can be started directly from the visible Support case

### Job continuity smoke

- create or open a guided Job demo workspace
- run one Job task if the workspace has no existing hiring packet yet
- confirm at least one Job hiring packet appears in the workbench
- confirm the latest packet event links back to the new task
- confirm the next shortlist refresh or review can be started directly from the visible Job hiring packet

These checks do not replace the smaller availability smoke. They extend it when the operator needs confidence that the
Stage E workbench depth still behaves honestly in the live demo.

## Viewer-Facing Explanation

The demo should now be described like this:

- the workspace keeps useful history instead of acting like a stateless playground
- new viewers should use a fresh guided demo workspace when a clean path matters
- existing Support work should continue from the visible case workbench
- existing Job work should continue from the visible hiring-packet workbench

That explanation is stronger and more honest than implying the system silently clears history between walkthroughs.
