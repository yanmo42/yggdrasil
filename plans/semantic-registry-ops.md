# Semantic Registry Operations

Status: planned
Owner: ian + ygg
Created: 2026-04-08
Program: `ygg-continuity-integration`

## Goal

Make `programs.json` and `ideas.json` first-class operational surfaces rather than mostly seeded/read-only state.

This phase should let Ygg explicitly create, update, and link semantic registry records from the CLI while keeping mutation legible and bounded.

## Why now

The repo now has:
- semantic registries
- continuity checkpoints
- runtime events
- topology-aware retrieval over those surfaces

The next bottleneck is not retrieval quality.
It is the lack of clean operator-facing mutation flows for the semantic layer itself.

## Deliverables

1. CLI mutation commands for `program` and `idea`
2. Shared validation + write helpers in `lib/ygg/semantic_registry.py`
3. Explicit link/update semantics
4. Tests for add/update/link flows
5. Docs for mutation contracts and examples

## Constraints

- No hidden automatic mutation of semantic registry state.
- Mutations must remain explicit and inspectable.
- Keep the JSON files authoritative.
- Prefer patch-style updates over magical rewrite behavior.
- Preserve stable ids and existing schema style.

## Phase 1 — Library support

Add registry write helpers for:
- load
- validate
- create item
- update item
- persist registry with updated `updatedAt`

Support only two kinds:
- `program`
- `idea`

## Phase 2 — CLI surface

Add explicit commands such as:
- `ygg program add`
- `ygg program update <id>`
- `ygg idea add`
- `ygg idea update <id>`
- `ygg idea link <id> --program ... --checkpoint ... --promotion-target ...`

If a matching `program link` command is useful, add it only when it improves symmetry rather than cluttering the surface.

## Phase 3 — Validation rules

At minimum validate:
- required ids and titles
- status vocabulary where already implied by docs
- list-vs-scalar fields
- link targets formatted consistently
- duplicate id prevention

## Phase 4 — Tests and docs

Add tests for:
- add success
- update success
- duplicate-id rejection
- missing-id update rejection
- link mutation behavior
- CLI text and JSON output where useful

Update docs so command contracts and examples are obvious.

## Definition of done

This phase is done when:
- semantic registry state can be mutated safely from the CLI,
- tests pass,
- docs are updated,
- and the workflow is more inspectable than manual JSON editing.
