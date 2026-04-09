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
- `ygg inventory`
- `ygg frontier` (`list`, `current`, `queue`, `sync`, `audit`, `open`)
- `ygg retrieve`
- `ygg retrieve-benchmark`
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
- `ygg heimdall`
- `ygg ratatoskr`

---

## Quick start

```bash
ygg --help
ygg explain suggest
ygg paths check
ygg suggest "implement the improved theme selector UX"
ygg inventory
ygg frontier sync
ygg frontier queue
ygg frontier audit
ygg frontier open --print-only
ygg retrieve "topology-aware continuity retrieval"
ygg retrieve-benchmark
ygg heimdall --show-json
ygg heimdall --note --ratatoskr
ygg ratatoskr --event-file /tmp/event.json
ygg raven launch "inspect environment drift"
ygg raven status
ygg status
ygg root "help me decide the next move"
```

For usage details, read:

- `docs/RUNNING.md`

---

## Start here

If you are new to Ygg, learn these first.

### The 5-command loop

This is the shortest path to using Ygg effectively:

```bash
ygg inventory
ygg status
ygg suggest "what I want"
ygg resume <domain> <task>
ygg forge --domain <domain> --task <task> "build the next thing"
```

### 10 most useful commands

1. `ygg inventory` — see what Ygg actually has right now.
2. `ygg frontier sync` + `ygg frontier queue` — hydrate the Ygg frontier queue from assistant-home batons, then inspect what is active vs ready.
3. `ygg frontier audit` — inspect the active Sandy Chaos frontier, proof debt, and next move.
3. `ygg status` — see what lanes/tasks are active.
4. `ygg suggest "..."` — turn a fuzzy request into likely Ygg commands.
5. `ygg root "..."` — stay in planner/spine mode when things are ambiguous.
6. `ygg work "..."` — use the flexible natural-language front door.
7. `ygg branch <domain> <task> ...` — create or refresh a tracked lane.
8. `ygg resume <domain> <task>` — reopen a known lane with continuity.
9. `ygg forge --domain <domain> --task <task> "..."` — push a lane toward implementation.
10. `ygg checkpoint ...` — record a structured continuity checkpoint.
11. `ygg paths` — inspect the path contract so you know what lives where.

### Common situations

**I feel lost**

```bash
ygg inventory
ygg status
```

**I know what I want, but not which command to use**

```bash
ygg suggest "continue the continuity integration work"
```

**I want to create a clean new lane**

```bash
ygg branch continuity inventory-surface \
  --objective "Build executable repo inventory for ygg" \
  --next-action "Add first query command"
```

**I want to pick up existing work**

```bash
ygg resume continuity inventory-surface
```

**I want to stop planning and build**

```bash
ygg forge --domain continuity --task inventory-surface \
  "implement the next useful query/edit command"
```

### Ignore these at first

Until the core loop feels natural, most people can ignore:

- `ygg raven`
- `ygg graft`
- `ygg beak`
- `ygg mode`
- `ygg nyx`
- `ygg heimdall`
- `ygg ratatoskr`

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
