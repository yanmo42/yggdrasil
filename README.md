# Ygg

A small home directory for the **Yggdrasil command family**.

## What this is

`~/ygg` is the human-facing control surface for the command system we have been designing around:

- **spine** — planner/control plane
- **branches** — bounded task lanes
- **promotion** — explicit return of meaningful branch outcomes
- **durable trace** — files/logs/batons that carry continuity across time

This directory exists to make the system easier to understand, inspect, and evolve.

## Important current reality

Ygg is now split into three package surfaces:

- `code/` — CLI code, tests, docs
- `machine/` — host bootstrap/setup scripts
- `state/` — state templates/policy + runtime output area

The planner/resume internals still depend on assistant-home modules in:

- `~/.openclaw/workspace-claw-main/scripts/work.py`
- `~/.openclaw/workspace-claw-main/tools/work_v1/`
- `~/.openclaw/workspace-claw-main/scripts/resume.py`
- `~/.openclaw/workspace-claw-main/state/resume/`

So this is a **packaged control plane** with a live dependency on the canonical spine workspace.

## Layout

- `code/` — portable CLI package (`code/src`, `code/bin`, `code/tests`, `code/docs`)
- `machine/` — portable host bootstrap package (`machine/bootstrap-host.sh`)
- `state/` — templates/policy + runtime state boundary (`state/templates`, `state/policy`, `state/runtime`)
- `bin/` — compatibility launcher shim (`bin/ygg` -> `code/bin/ygg`)
- `src/`, `tests/`, `docs/` — compatibility symlinks to `code/*`
- `links/` — local symlinks to assistant-home implementation pointers

## Naming

- **Architecture name:** Yggdrasil
- **CLI namespace:** `ygg`
- **Style rule:** poetic topology, clear action semantics

## First files to read

1. `code/docs/NORTH-STAR.md`
2. `code/docs/RAVENS.md`
3. `code/docs/RAVENS-V1.md`
4. `code/docs/VOCAB.md`
5. `code/docs/VERBS.md`
6. `code/docs/CONTRACTS.md`
7. `code/docs/CONTINUITY-OPS-V1.md`
8. `code/docs/RUNNING.md`
9. `code/docs/ARCHITECTURE.md`
10. `code/docs/ROADMAP.md`
11. `SECURITY.md`
12. `code/src/cli.py`
13. `machine/bootstrap-host.sh`
14. `state/policy/STATE-BOUNDARY.md`

## Current CLI status

A usable prototype entrypoint exists at:

- `~/ygg/bin/ygg`
- exposed on PATH as `ygg` via `~/.local/bin/ygg`

Current verbs:

- `ygg explain`
- `ygg help` (alias of `explain`)
- `ygg suggest`
- `ygg work`
- `ygg paths` (path-contract show/check)
- `ygg raven` (launch/status/inspect/return)
- `ygg graft` (propose)
- `ygg beak` (propose)
- `ygg root`
- `ygg branch`
- `ygg resume`
- `ygg forge`
- `ygg promote`
- `ygg status`

## Quick start

```bash
ygg --help
ygg explain suggest
ygg help promote
ygg paths check
ygg raven launch "inspect environment drift"
ygg suggest "implement the improved theme selector UX"
ygg status
ygg root "help me decide the next move"
```

For more details, read:

- `docs/RUNNING.md`

## Why this directory exists

The point is not just convenience.
A clear filesystem shape helps the human operator:

- understand what the system is
- inspect current code paths
- see what is stable vs planned
- follow architectural evolution without spelunking the entire assistant workspace
