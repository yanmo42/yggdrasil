# Ygg Architecture

## Purpose

Ygg is a **local operator-facing control plane** for branching work.
It is designed first for legibility and reliable use on our own Unix systems, not for abstract packaging purity or mainstream distribution.

The filesystem should explain the system.
A person should be able to inspect `~/ygg` and immediately infer:

- how Ygg is invoked
- where implementation lives
- where command vocabulary lives
- where machine/bootstrap logic lives
- where mutable runtime state lives
- where to read the architecture

## Architectural stance

Ygg is not trying to be a generic public Python package first.
It is trying to be:

- **architecturally obvious**
- **Unix-legible**
- **portable across simple Unix environments**
- **clear to both the human operator and the assistant**

That means:

- top-level directories should map to real system roles
- there should be one canonical path for each class of artifact
- mutable state must be visibly separate from implementation
- compatibility shims may exist, but should not define the architecture

## Canonical top-level taxonomy

```text
~/ygg/
  bin/        # stable executable entrypoints
  lib/        # implementation library code
  commands/   # command vocabulary / verb surfaces
  docs/       # architecture and operator-facing docs
  tests/      # validation of Ygg behavior/contracts
  machine/    # host/bootstrap/setup logic
  state/      # mutable runtime state, policy, templates, scripts
  links/      # explicit bridges to assistant-home or external canonical surfaces
```

## Directory roles

### `bin/`
Stable executable front doors.

Rule:
- `bin/` should stay boring.
- A Unix operator should be able to run Ygg without understanding the whole internals.

Current canonical entrypoint:
- `bin/ygg`

### `lib/`
Implementation library code.

Rule:
- executable logic should live here, not in `bin/`
- use a namespaced module layout when practical

Canonical implementation root:
- `lib/ygg/`

This keeps the implementation visually separate from:
- command docs/contracts
- mutable state
- machine bootstrap logic

### `commands/`
Human-facing command vocabulary and verb-specific surfaces.

This is top-level because Ygg is conceptually organized around verbs and bounded operations, not just around Python modules.

Examples:
- `commands/raven/`
- `commands/graft/`
- `commands/beak/`
- `commands/spine/`

These paths are lightweight command-surface wrappers over the canonical `bin/ygg` + `lib/ygg` implementation.
They exist for legibility and topology, not as a second implementation stack.

### `docs/`
Human orientation and architectural explanation.

Docs are top-level because Ygg is architecture-heavy and operator-driven.
A user should not have to spelunk implementation directories to understand the system.

Key docs live here:
- `docs/ARCHITECTURE.md`
- `docs/NORTH-STAR.md`
- `docs/RUNNING.md`
- `docs/CONTRACTS.md`
- `docs/VOCAB.md`
- `docs/VERBS.md`

### `tests/`
Behavioral and contract validation.

Rule:
- tests should be easy to find
- test paths should point at canonical implementation paths

### `machine/`
Machine/bootstrap/setup logic.

This is where host-specific setup belongs.
It is intentionally separated from both implementation and mutable state.

Examples:
- bootstrap scripts
- install helpers
- host preparation steps

### `state/`
Mutable runtime world.

This is one of the most important boundaries in Ygg.

`state/` holds things that change during operation, such as:
- runtime output
- logs
- policy artifacts
- templates
- support scripts tied to state handling

Implementation code must not be confused with mutable runtime artifacts.
That separation is necessary for inspectability and sane Unix operation.

### `links/`
Explicit bridge points to external canonical surfaces.

This exists because Ygg is still partly connected to assistant-home internals in the OpenClaw workspace.
Those bridges should be visible and documented rather than implicit.

## System strata

Ygg consists of four visible strata:

### 1. Interface / invocation
- `bin/`
- `commands/`

### 2. Implementation
- `lib/ygg/`

### 3. Environment / runtime
- `machine/`
- `state/`
- `links/`

### 4. Human orientation
- `docs/`

This structure is the architectural truth the repository should expose.

## Packaging principle

The packaging principle is:

> **operator-legible packaging**

Meaning:
- the filesystem should explain the system
- names should match how we talk about the system
- there should be a single canonical path per thing
- portability should increase clarity, not reduce it

## Conventions and rules

### Canonical path rule
Each artifact class gets one canonical home.
Avoid mirrored directory trees.
Avoid making two paths look equally authoritative.

### Compatibility rule
Compatibility shims are allowed during migration, but they are not the architecture.
If a shim exists, the canonical path should still be obvious.

### Unix portability rule
Prefer:
- simple launchers
- stable relative pathing
- ordinary directory names
- minimal hidden magic

Avoid:
- packaging cleverness that obscures the real structure
- unnecessary symlink mirrors
- coupling runtime state to implementation layout

### Naming rule
Top-level names should reflect **system role**, not vague meta-categories.

Good:
- `bin`
- `lib`
- `commands`
- `docs`
- `tests`
- `machine`
- `state`

Weak:
- `code`

`code` is too generic to carry architectural meaning.

## Current implementation relationship

Ygg is still a packaged control-plane layer with live dependencies on assistant-home internals in the canonical OpenClaw workspace.
That is acceptable in the short term, as long as those dependencies are explicit and inspectable.

Current dependency areas include planner/resume internals in assistant-home.
These should be documented clearly and reduced over time only when doing so improves real clarity or portability.

## Failure conditions

The architecture is failing if:

- a human cannot tell which path is canonical
- the directory tree needs too much explanation before it makes sense
- mutable state and implementation blur together
- compatibility layers become permanent structural confusion
- portability work makes local operation harder to understand
- a new file has no obvious home

## Design goal for ongoing development

When changing Ygg, prefer the option that makes the repo more self-explanatory at a glance.
The tree itself should communicate the architecture.
