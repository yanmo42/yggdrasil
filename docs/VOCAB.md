# Vocabulary

## Core naming

- **Yggdrasil** — the architecture / continuity model
- **ygg** — the CLI namespace / shell entrypoint
- **spine** — the planner/control plane
- **branch** — a bounded task lane or local work process
- **promotion** — explicit movement of branch outcomes toward durable surfaces
- **durable trace** — any artifact that preserves continuity across time
- **lane** — an execution role or task path inside a branch
- **contract** — a bounded task definition with constraints and validation

## Verb design rule

The system should be poetic in **topology, cadence, and consequence** before it is poetic in ornament.

So:

- nouns may be symbolic
- verbs should stay operationally clear

## Recommended verb family

- `ygg explain` — self-teaching vocabulary for Ygg verbs
- `ygg suggest` — translate natural-language intent into candidate Ygg commands
- `ygg work` — natural-language front door
- `ygg root` — force planner spine / no routing guess
- `ygg branch` — create or refresh an explicit lane in baton state
- `ygg resume` — continuity-biased reopen of a lane
- `ygg forge` — planner-supervised implementation/delegation entry
- `ygg promote` — explicit branch disposition / promotion record
- `ygg status` — inspect tracked domains and tasks

See `docs/VERBS.md` for exact v1 semantics.

## Working command semantics

### `explain`
Use when the human needs a quick refresher on what a verb does.
Should provide self-teaching guidance with examples.

### `suggest`
Use when the human wants natural language help before committing to a command.
Should interpret intent and propose a small set of explicit next commands.

### `work`
Use when the user wants a flexible front door.
May classify intent and open planner spine with routing context.

### `root`
Use when the human wants the control plane directly.
No aggressive route guessing.

### `branch`
Use when the human knows this is separate from current active work.
Should create or refresh a separate lane with clear contract boundaries.

### `resume`
Use when continuity with existing work is the main concern.
Bias toward the correct active lane.

### `forge`
Use when the next move is implementation, building, fixing, or delegation.
Should still remain spine-supervised.

### `promote`
Use when a branch outcome must be classified and returned to durable surfaces.
Expected dispositions may include:

- `no-promote`
- `log-daily`
- `promote-durable`
- `escalate-hitl`

### `status`
Use to inspect current baton state and active lanes.

## Anti-pattern

Do not let poetic naming obscure action semantics.

Bad pattern:
- `ygg sap`
- `ygg leafsong`
- `ygg rootspeech`

These may be fun aliases later, but they should not be the primary operating surface.
