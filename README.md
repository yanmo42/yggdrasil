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

This is a **clean scaffold and documentation home**.
The current authoritative implementation still lives in:

- `~/.openclaw/workspace-claw-main/scripts/work.py`
- `~/.openclaw/workspace-claw-main/tools/work_v1/`
- `~/.openclaw/workspace-claw-main/scripts/resume.py`
- `~/.openclaw/workspace-claw-main/state/resume/`

This means:

- `~/ygg` is the best place to **follow along**
- the existing workspace remains the current source of truth
- a future migration into `~/ygg/src/` can happen once the vocabulary/spec settles

## Layout

- `bin/` — entrypoint scripts
- `src/` — Ygg CLI/source code
- `docs/` — architecture, vocabulary, verb semantics, running instructions, roadmap
- `state/` — Ygg-local machine-readable records (created on demand)
- `links/` — symlinks to current implementation in assistant-home
- `notes/` — scratch notes and human-readable promotion records

## Naming

- **Architecture name:** Yggdrasil
- **CLI namespace:** `ygg`
- **Style rule:** poetic topology, clear action semantics

## First files to read

1. `docs/VOCAB.md`
2. `docs/VERBS.md`
3. `docs/RUNNING.md`
4. `docs/ARCHITECTURE.md`
5. `docs/ROADMAP.md`
6. `SECURITY.md`
7. `src/cli.py`
8. `links/`

## Current CLI status

A usable prototype entrypoint exists at:

- `~/ygg/bin/ygg`
- exposed on PATH as `ygg` via `~/.local/bin/ygg`

Current verbs:

- `ygg explain`
- `ygg suggest`
- `ygg work`
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
