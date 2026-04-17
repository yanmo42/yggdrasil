# Bridge Ownership Tightening

Status: planned
Owner: ian + ygg
Created: 2026-04-08
Program: `ygg-continuity-integration`

## Goal

Tighten the ownership boundary between:
- Ygg-owned canonical repo state
- Ygg-derived or runtime state
- assistant-home / OpenClaw local state
- Sandy Chaos canonical research state
- bridge surfaces that connect them

The point is to make future features safer and more legible, not merely more powerful.

## Why now

The repo now has:
- semantic continuity state
- topology-aware retrieval
- semantic registry mutation commands

That means ambiguity about ownership is now the bigger risk than missing capability.

## Deliverables

1. One explicit bridge ownership contract doc
2. Inventory/system descriptions updated to reflect ownership classes
3. Command/docs wording tightened where mutation authority matters
4. Tests covering the new ownership surfaces where appropriate

## Constraints

- Do not pretend Ygg owns Sandy Chaos canon
- Do not pretend assistant-home runtime memory is canonical repo truth
- Keep canonical vs derived vs runtime distinctions explicit
- Prefer a small number of clear ownership classes over a sprawling taxonomy

## Ownership classes

Use a small operational classification set:
- `ygg-canonical`
- `ygg-derived`
- `assistant-local`
- `sc-canonical`
- `bridge`

## Phase 1 — Contract

Write a single doc that states:
- which paths/surfaces belong to which class
- what each class is allowed to do
- who may mutate each class
- examples of canonical vs derived vs runtime outputs

## Phase 2 — Inventory + command surface

Update inventory/system summaries and any CLI/help/contract text so the ownership split is visible in:
- repo inventory
- semantic continuity descriptions
- runtime courier descriptions
- state boundary language

## Phase 3 — Validation

Add or update tests so:
- ownership categories present in inventory remain stable
- command/help contracts reflect the tightened boundary
- no existing command falsely suggests authority it does not have

## Definition of done

This is done when:
- ownership is stated in one authoritative repo doc
- inventory and command surfaces reflect it
- tests pass
- future work can build on a clearer boundary than the repo had before
