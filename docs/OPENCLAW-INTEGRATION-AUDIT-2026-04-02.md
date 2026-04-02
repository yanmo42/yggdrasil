# OpenClaw Integration Audit — 2026-04-02

## Goal

Reconcile the new Ygg continuity work created in `~/.openclaw/workspace-claw-main` against the canonical Ygg repo at `~/ygg`, so Ygg can become a shippable rolling release while keeping OpenClaw dependencies explicit.

This is a Phase 1 audit artifact:
- inspect
- classify
- decide ownership
- prepare promotion/move work

Not yet:
- move files
- rewrite imports
- commit/push

---

## Current architectural baseline

Existing Ygg docs already establish this stance:

- `~/ygg` is the **canonical operator-facing control-plane home**.
- assistant-home (`~/.openclaw/workspace-claw-main`) still owns some **spine/runtime internals**.
- the dependency boundary should remain **explicit, inspectable, and honest**.

Relevant existing docs:
- `README.md`
- `docs/DEPENDENCIES.md`
- `links/README.md`
- `state/policy/STATE-BOUNDARY.md`

This means the question is **not** “make Ygg fake-completely-self-contained.”
The real question is:

> Which of the newly created continuity artifacts are truly Ygg-owned, and which are assistant-home-owned runtime surfaces or local state?

---

## Verified workspace artifacts created/updated this morning

From assistant-home:

### Docs / contracts
- `core/YGG.md`
- `core/YGG-OPERATING-BASELINE.md`
- `core/RATATOSKR.md`

### Executable wrappers
- `scripts/heimdall.py`
- `scripts/ratatoskr.py`

### Library code
- `tools/heimdall_v1/runtime.py`
- `tools/ratatoskr_v1/runtime.py`

### Tests
- `tests/test_heimdall.py`
- `tests/test_ratatoskr.py`

### State / runtime snapshot
- `state/ygg-self.json`

### Also updated conceptually
- `AGENTS.md`
- `core/MEMORY.md`
- daily memory entries for 2026-04-02

---

## What already exists in `~/ygg`

Ygg already has:
- a documented dependency boundary (`docs/DEPENDENCIES.md`)
- an explicit bridge surface (`links/README.md`)
- a commit-safe state boundary (`state/README.md`, `state/policy/STATE-BOUNDARY.md`)
- continuity-adjacent operational docs (`docs/CONTINUITY-OPS-V1.md`)
- tests, docs, commands, machine scripts, and state package layout

Ygg also currently has untracked content under:
- `state/ygg/`

Initial inspection evidence confirms this directory already contains structured continuity/project-state material rather than just runtime embodiment data. One observed record includes a concept/promotion-style payload for:
- `"topology-aware continuity retrieval over the current ecosystem"`
- disposition: `TODO_PROMOTE`
- promotion target: `docs/archive/topological_memory_continuity_retrieval_v0.md`
- next action: `Build 30-query benchmark against keyword, recency, and embedding baselines`

So `state/ygg/` is not empty noise; it appears to be the beginning of the exact higher-level semantic layer Ian was asking for (ideas / programs / promotion candidates / continuity-topology material).

---

## Classification

## A. Promote into `~/ygg` as Ygg-owned product logic

These look like genuine Ygg control-plane / continuity features and should likely live in `~/ygg` rather than only in assistant-home.

### 1. Heimdall runtime refresh logic
Current assistant-home files:
- `scripts/heimdall.py`
- `tools/heimdall_v1/runtime.py`
- `tests/test_heimdall.py`

Reason:
- this is general Ygg continuity/runtime-refresh logic
- it models embodiment state rather than chat-local personality only
- it belongs closer to Ygg’s continuity system than to one specific assistant-home workspace

Promote target in `~/ygg`:
- likely `lib/ygg/heimdall.py` or `lib/ygg/continuity/heimdall.py`
- CLI hook via `bin/ygg` / verb namespace or a stable helper wrapper
- tests under `~/ygg/tests/`

Notes:
- current implementation imports assistant-home utilities (`tools.resume_v1.*`), so promotion is not a pure file copy
- this needs dependency disentangling in Phase 2

### 2. Ratatoskr continuity courier logic
Current assistant-home files:
- `scripts/ratatoskr.py`
- `tools/ratatoskr_v1/runtime.py`
- `tests/test_ratatoskr.py`

Reason:
- this is a general continuity event-routing abstraction
- it reads like Ygg-owned architecture, not a one-off workspace helper
- if Ygg is the canonical control plane, structured continuity routing should be represented there

Promote target in `~/ygg`:
- likely `lib/ygg/ratatoskr.py` or `lib/ygg/continuity/ratatoskr.py`
- test coverage in `~/ygg/tests/`
- doc references in `docs/`

Notes:
- current routing destinations are assistant-home paths like `memory/daily`
- Ygg needs either a portable event sink contract or explicit dual-target behavior

### 3. Continuity contracts as Ygg docs
Current assistant-home docs:
- `core/YGG.md`
- `core/YGG-OPERATING-BASELINE.md`
- `core/RATATOSKR.md`

Reason:
- these define architecture-level continuity concepts
- they should not exist only inside assistant-home if Ygg is the canonical product/repo

Promote target in `~/ygg`:
- probably `docs/` with names adjusted for repo style, e.g.
  - `docs/YGG-CONTINUITY.md`
  - `docs/YGG-OPERATING-BASELINE.md`
  - `docs/RATATOSKR.md`

Notes:
- assistant-home may still keep local copies or shorter operator versions, but repo-owned canonical docs should exist in `~/ygg`

---

## B. Keep in assistant-home as local runtime state / embodiment data

### 1. `state/ygg-self.json`
Reason:
- this contains runtime embodiment snapshot data for the current live environment
- that is local machine/runtime state, not canonical repo content
- Ygg’s existing state policy already says runtime outputs belong under `state/runtime/` and should not be committed blindly

Decision:
- do **not** copy this literal file into git as-is as core product content
- instead, define:
  - a committed schema/template/example in `~/ygg`
  - and a runtime-generated actual state file outside committed state, probably under `~/ygg/state/runtime/` or a clearly documented local path

### 2. `AGENTS.md`, `core/MEMORY.md`, daily memory entries
Reason:
- these are assistant-home identity/memory surfaces
- they are local continuity/persona/runtime records, not Ygg product source files

Decision:
- keep local
- only promote the architecture concepts, not the actual live memory contents

---

## C. Bridge/document, but do not blindly move yet

### 1. Daily memory writing behavior
Heimdall/Ratatoskr currently write into assistant-home memory surfaces such as:
- `memory/daily/YYYY-MM-DD.md`
- `memory/promotion-candidates.md`

Reason:
- those destinations are specific to the assistant-home continuity setup
- Ygg may eventually support them, but they are not automatically portable as repo-local product behavior

Decision:
- document this as an integration path
- do not hard-code assistant-home-only paths as the only Ygg behavior
- likely refactor toward targetable sinks:
  - assistant-home memory sink
  - Ygg-local notes sink
  - promotion artifact sink

### 2. Imports from assistant-home `tools.resume_v1.*`
Observed in current workspace implementation:
- `tools.heimdall_v1.runtime` imports `tools.resume_v1.daily` and `tools.resume_v1.util`
- `tools.ratatoskr_v1.runtime` imports the same assistant-home helpers

Reason:
- this proves the new code is not yet repo-portable
- it depends on assistant-home helper modules that are not part of `~/ygg`

Decision:
- this is the main technical gap before promotion
- Phase 2 should replace these imports with one of:
  1. Ygg-local utility functions
  2. a small shared library contract
  3. adapter shims with explicit bridge docs

### 3. `state/ygg/` in `~/ygg`
Reason:
- this directory is already untracked in `~/ygg`
- inspection evidence shows it contains semantic continuity/project-state material
- it may represent an earlier or parallel attempt at exactly the missing `ideas` / `active programs` layer
- it could conflict with, complement, or supersede parts of the new design

Observed signal:
- concept/promotion record for `topology-aware continuity retrieval over the current ecosystem`
- disposition marked `TODO_PROMOTE`
- explicit promotion target into repo docs

Decision:
- treat `state/ygg/` as a serious candidate canonical home for semantic Ygg state
- compare it directly against the new assistant-home continuity work before moving anything
- likely split becomes:
  - `state/ygg/` = semantic/operational Ygg state (ideas, programs, promotion candidates, topology)
  - Heimdall/Ratatoskr = runtime refresh + continuity courier layer
  - `ygg-self.json` = local embodiment snapshot, not canonical semantic program-state

---

## Focused inventory result: what already exists in `~/ygg`

A deeper read of the repo shows that `~/ygg` already has a **minimal semantic continuity subsystem**.

### Existing semantic-state implementation

Files:
- `lib/ygg/continuity.py`
- `tests/test_continuity.py`
- `lib/ygg/cli.py` (`checkpoint`, `promote`, `status --continuity`)

Current model:
- canonical storage path: `~/ygg/state/ygg/checkpoints/*.json`
- checkpoint shape:
  - `timestamp`
  - `lane`
  - `summary`
  - `disposition`
  - `promotion_target`
  - `evidence`
  - `next_action`

Current supported dispositions:
- `DROP_LOCAL`
- `LOG_ONLY`
- `TODO_PROMOTE`
- `DOC_PROMOTE`
- `POLICY_PROMOTE`
- `ESCALATE`

Current capabilities already wired into the CLI:
- `ygg checkpoint`
- `ygg promote --lane ... --summary ... --disposition ...`
- `ygg status --continuity`

### What `state/ygg/` currently is

Not a full registry yet.
It is currently a **checkpoint ledger for semantic continuity decisions**.

That means:
- it already has a canonical home
- it already has code ownership in `~/ygg`
- it already has tests
- but it does **not yet** model a full inventory of ideas/programs/topology

### Important architectural implication

The repo does **not** need a brand new semantic-state subsystem invented from scratch.
It needs an **extension of the existing continuity subsystem**.

Best interpretation now:
- `lib/ygg/continuity.py` = seed semantic continuity kernel
- `state/ygg/checkpoints/` = canonical semantic continuity artifact store
- missing next layer = richer structured models for:
  - active programs
  - ideas
  - maybe topology / relationships between lanes
- Heimdall/Ratatoskr = separate runtime-continuity infrastructure that should integrate with, not replace, this subsystem

## Current recommendation for Phase 2

### Promote as product concepts
Into `~/ygg`:
- Heimdall concept + implementation
- Ratatoskr concept + implementation
- continuity docs/contracts
- tests
- a portable state/schema contract

### Keep local-only
In assistant-home:
- live `ygg-self.json` snapshot
- daily memory logs
- persona and relationship memory
- machine-specific runtime history

### Refactor before promotion
Required before the move is considered clean:
- remove assistant-home-only imports from Heimdall/Ratatoskr
- define portable output destinations and/or adapters
- clarify whether Ygg-local runtime state should live in:
  - `~/ygg/state/runtime/`, or
  - assistant-home only, with Ygg just documenting the contract

---

## Provisional move checklist

1. Inspect `~/ygg/state/ygg/`
2. Decide canonical Ygg module layout for continuity features
3. Port Heimdall logic into `~/ygg` with no assistant-home-only imports
4. Port Ratatoskr logic into `~/ygg` with pluggable sinks
5. Convert `core/*.md` continuity docs into canonical `~/ygg/docs/*`
6. Add an example/template for runtime self state instead of committing the live snapshot directly
7. Update `README.md` and `docs/DEPENDENCIES.md` to describe the new boundary
8. Run tests
9. Commit/push

---

## Current bottom line

The new continuity work is **real** and **useful**, but it is currently split across the wrong boundary for release purposes.

Best interpretation:
- **architecture + logic** should move toward `~/ygg`
- **live memory/runtime snapshots** should stay local
- **assistant-home imports** are the main portability blocker

That means the repo is not yet at “ready to release,” but the path to get there is now much clearer.
