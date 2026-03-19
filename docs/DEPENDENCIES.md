# Ygg Dependency Boundary

This file defines the current boundary between:

- **Ygg** as the local operator-facing control plane in `~/ygg`
- **assistant-home / spine** as the canonical OpenClaw workspace in `~/.openclaw/workspace-claw-main`

The goal is to make the bridge explicit.
Not everything should be moved into Ygg.
But anything Ygg depends on should be visible, named, and justified.

---

## Boundary summary

Ygg currently owns:

- its local launcher surface (`bin/`)
- its implementation library (`lib/ygg/`)
- its topological command surface (`commands/`)
- its architecture/operator docs (`docs/`)
- its local tests (`tests/`)
- its machine/bootstrap logic (`machine/`)
- its own runtime/policy/templates boundary (`state/`)

Assistant-home currently still owns core spine machinery for:

- planner packet assembly
- route classification heuristics used by planner entry
- baton store / resume state operations
- active-task indexing and continuity reopening

That means:

> Ygg is the legible control-plane shell.
> Assistant-home still owns some canonical spine internals.

---

## Live bridge surfaces

The `links/` directory points at the current assistant-home dependency surfaces:

- `links/work.py` -> `~/.openclaw/workspace-claw-main/scripts/work.py`
- `links/resume.py` -> `~/.openclaw/workspace-claw-main/scripts/resume.py`
- `links/router.py` -> `~/.openclaw/workspace-claw-main/tools/work_v1/router.py`
- `links/planner.py` -> `~/.openclaw/workspace-claw-main/tools/work_v1/planner.py`
- `links/workspace-claw-main` -> `~/.openclaw/workspace-claw-main`

These links exist for inspectability.
They are not the canonical implementation of Ygg itself.

---

## Dependency table

## 1. `scripts/work.py`
Path:
- `~/.openclaw/workspace-claw-main/scripts/work.py`

Role:
- planner-facing natural-language front door
- route selection + planner packet launch path

Why Ygg depends on it:
- `ygg work` intentionally forwards into the active planner-spine wrapper rather than reimplementing planner launch semantics separately

Canonical owner today:
- assistant-home / spine

Why it is still external:
- it is tightly coupled to the current OpenClaw planner session behavior and shared workspace policy

Move into Ygg later only if:
- planner launch behavior becomes Ygg-owned rather than assistant-home-owned
- or the planner boot protocol stabilizes enough to deserve a true Ygg-local implementation

Failure condition:
- Ygg and assistant-home diverge on what `work` means
- or `ygg work` becomes a thin alias over behavior nobody can easily inspect from Ygg docs

Current stance:
- **Defensible now:** keep external
- **Plausible later:** absorb into Ygg only if planner ownership moves

---

## 2. `scripts/resume.py`
Path:
- `~/.openclaw/workspace-claw-main/scripts/resume.py`

Role:
- baton-aware checkpoint/open/status/finish CLI
- continuity reopening and task-lane state management

Why Ygg depends on it:
- `ygg branch`, `ygg resume`, `ygg status`, and parts of `ygg promote` rely on the current baton model

Canonical owner today:
- assistant-home / spine

Why it is still external:
- resume state is part of the canonical hot continuity system, not just a Ygg-local convenience

Move into Ygg later only if:
- Ygg becomes the canonical owner of baton continuity
- or resume state is intentionally split into a transport-neutral library used by both systems

Failure condition:
- Ygg appears to own branches/resume conceptually, but the actual continuity behavior can only be understood from assistant-home internals

Current stance:
- **Defensible now:** keep external
- **Plausible later:** factor shared baton logic into a common library before moving ownership

---

## 3. `tools/work_v1/router.py`
Path:
- `~/.openclaw/workspace-claw-main/tools/work_v1/router.py`

Role:
- request classification heuristics
- route suggestions for planner entry

Why Ygg depends on it:
- `ygg suggest` and forced planner-entry flows rely on the same routing heuristics as the broader work front door

Canonical owner today:
- assistant-home / spine

Why it is still external:
- route heuristics are still part of the broader planner/work orchestration system, not a clearly separated Ygg-local policy module

Move into Ygg later only if:
- Ygg becomes the canonical home of route semantics
- or router logic is stabilized into a shared library with explicit ownership

Failure condition:
- Ygg presents a command-language surface whose suggestion behavior drifts away from the actual planner routing logic

Current stance:
- **Defensible now:** keep external
- **Plausible later:** extract to shared library or move once route semantics are clearly Ygg-owned

---

## 4. `tools/work_v1/planner.py`
Path:
- `~/.openclaw/workspace-claw-main/tools/work_v1/planner.py`

Role:
- active-task loading
- planner boot packet assembly
- routing context rendering

Why Ygg depends on it:
- `ygg root`, `ygg forge`, and `ygg suggest` use planner packet construction and active-task inspection directly

Canonical owner today:
- assistant-home / spine

Why it is still external:
- the planner boot packet is still a spine concern more than a Ygg concern

Move into Ygg later only if:
- planner boot packet structure becomes a stable control-plane contract owned by Ygg
- or planner state loading is intentionally separated from assistant-home runtime specifics

Failure condition:
- Ygg appears to have its own planner surface, but packet semantics can only be reasoned about by reading assistant-home tools

Current stance:
- **Defensible now:** keep external
- **Plausible later:** extract shared planner-contract library first

---

## 5. `state/resume/`
Path:
- `~/.openclaw/workspace-claw-main/state/resume/`

Role:
- canonical baton store / continuity state
- task/domain index + active lane tracking

Why Ygg depends on it:
- Ygg lane verbs are only useful if they operate on the same continuity substrate as the planner spine

Canonical owner today:
- assistant-home / spine

Why it is still external:
- this is currently canonical runtime continuity, not just Ygg-local cache or mirror data

Move into Ygg later only if:
- continuity ownership deliberately shifts into Ygg
- or the baton store is made explicitly shared with a stable ownership contract

Failure condition:
- users think Ygg owns state while the authoritative lane truth actually lives elsewhere

Current stance:
- **Defensible now:** keep external
- **Probably not first move:** do not move this before route/planner ownership is clarified

---

## What should *not* be moved just for tidiness

Do not move a dependency into Ygg merely because:

- it would make the repo look more self-contained
- the path feels aesthetically cleaner
- we want fewer references into assistant-home

A move is justified only if it improves one of:

- clarity of ownership
- portability
- inspectability
- stability of contracts

---

## Recommended evolution path

### Phase 1 — explicit bridge (current goal)
- document all live dependencies
- keep ownership honest
- keep links visible

### Phase 2 — identify stable shared contracts
Possible extraction candidates:
- route classification contract
- planner boot packet schema
- baton-store interface

### Phase 3 — move only after ownership is clear
Only move functionality into Ygg when one of these becomes true:
- Ygg is the rightful canonical owner
- the dependency can be factored into a shared library with clear boundary semantics

---

## Architectural rule

If a human asks:

> “Is this part of Ygg, or part of the spine?”

there should be a short, non-handwavy answer.

If there is not, the boundary is under-specified.
