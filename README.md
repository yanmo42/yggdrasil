# Ygg

Ygg is the **local operator-facing control plane** for the Yggdrasil command family.

It is meant to be:

- architecturally obvious
- Unix-legible
- easy for both Ian and the assistant to inspect
- portable across ordinary Unix-like systems without turning into packaging theater

The main rule is simple:

> **the filesystem should explain the system**

---

## What Ygg is for

`~/ygg` is the human-facing home for the command system built around:

- **spine** — planner / control plane
- **branches** — bounded task lanes
- **promotion** — explicit return of meaningful branch outcomes
- **durable trace** — files, logs, and artifacts that preserve continuity across time

This directory exists so the system is easier to:

- understand
- inspect
- operate
- evolve

without having to spelunk the whole assistant workspace every time.

---

## Architectural stance

Ygg is **not** primarily optimized as a generic public package.
It is optimized first as a **clear local Unix control plane**.

That means:

- top-level directories should map to real system roles
- each artifact class should have one canonical home
- mutable state should stay visibly separate from implementation
- compatibility shims are allowed, but should not define the architecture

For the deeper rationale, read:

- `docs/ARCHITECTURE.md`
- `docs/DEPENDENCIES.md`

---

## Canonical layout

```text
~/ygg/
  bin/        # stable executable entrypoints
  lib/        # implementation library code
  commands/   # command-surface wrappers / verb topology
  docs/       # architecture and operator-facing docs
  tests/      # validation of Ygg behavior/contracts
  machine/    # host/bootstrap/setup logic
  state/      # mutable runtime state, policy, templates, scripts
  links/      # explicit bridges to assistant-home / external canonical surfaces
```

### Directory roles

- `bin/` — stable front doors; should stay boring
- `lib/` — canonical implementation (`lib/ygg/`)
- `commands/` — topological command surface; thin wrappers over `bin/ygg`
- `docs/` — architecture, concepts, usage, and operator docs
- `tests/` — behavioral and contract validation
- `machine/` — machine/bootstrap scripts
- `state/` — mutable runtime world
- `links/` — explicit bridges to assistant-home internals

---

## What is canonical right now

### Canonical entrypoint

- `~/ygg/bin/ygg`
- exposed on PATH as `ygg` via `~/.local/bin/ygg`

### Canonical implementation

- `~/ygg/lib/ygg/`

### Canonical command surface

- `~/ygg/commands/`

Important:
`commands/` is a **wrapper surface**, not a second implementation stack.
If logic starts diverging between `commands/` and `lib/ygg/`, the architecture is drifting.

### Canonical mutable state boundary

- `~/ygg/state/`

---

## Current reality: Ygg still bridges into assistant-home

Ygg is the clean control-plane surface, but some planner/resume internals still live in the OpenClaw assistant-home workspace.

Current dependency areas include:

- `~/.openclaw/workspace-claw-main/scripts/work.py`
- `~/.openclaw/workspace-claw-main/tools/work_v1/`
- `~/.openclaw/workspace-claw-main/scripts/resume.py`
- `~/.openclaw/workspace-claw-main/state/resume/`

So, in plain terms:

> Ygg is the legible front door.
> Some canonical spine machinery still lives in assistant-home.

That is acceptable for now as long as the dependency stays explicit and inspectable.

---

## Naming

- **Architecture name:** Yggdrasil
- **CLI namespace:** `ygg`
- **Style rule:** poetic topology, clear action semantics

---

## First files to read

1. `docs/ARCHITECTURE.md`
2. `docs/NORTH-STAR.md`
3. `docs/RUNNING.md`
4. `docs/VERBS.md`
5. `docs/CONTRACTS.md`
6. `docs/RAVENS.md`
7. `docs/RAVENS-V1.md`
8. `docs/VOCAB.md`
9. `docs/CONTINUITY-OPS-V1.md`
10. `docs/ROADMAP.md`
11. `SECURITY.md`
12. `lib/ygg/cli.py`
13. `docs/DEPENDENCIES.md`
14. `commands/README.md`
15. `links/README.md`
16. `machine/bootstrap-host.sh`
17. `state/policy/STATE-BOUNDARY.md`

---

## Current CLI status

A usable prototype entrypoint exists now.

Current verbs:

- `ygg explain`
- `ygg help` (alias of `explain`)
- `ygg suggest`
- `ygg work`
- `ygg paths`
- `ygg raven` (`launch`, `status`, `inspect`, `return`, `adjudicate`)
- `ygg graft` (`propose`)
- `ygg beak` (`propose`)
- `ygg root`
- `ygg branch`
- `ygg resume`
- `ygg forge`
- `ygg promote`
- `ygg status`
- `ygg mode`

---

## Quick start

```bash
ygg --help
ygg explain suggest
ygg paths check
ygg suggest "implement the improved theme selector UX"
ygg raven launch "inspect environment drift"
ygg raven status
ygg status
ygg root "help me decide the next move"
```

For usage details, read:

- `docs/RUNNING.md`

---

## Design intent

The point of this directory is not just convenience.
It is to make the control plane visible in the tree itself.

A good Ygg layout should let a human quickly answer:

- How do I run it?
- Where is the real implementation?
- Where do commands live conceptually?
- Where does state go?
- What is machine-specific?
- What still depends on assistant-home?

If the tree stops answering those questions clearly, the architecture needs work.
