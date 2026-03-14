# Verb Spec (Ygg v1)

This file defines what each `ygg` verb is supposed to do **before** implementation details drift.

## Design rule

The command family should be poetic in **topology, cadence, and consequence** while remaining clear in **action semantics**.

That means:

- the ontology may be symbolic (`spine`, `branch`, `promotion`)
- the verbs should still tell the truth about what they do

---

## `ygg work`

### Purpose
Natural-language front door into the planner spine.

### v1 behavior
- forwards to the current planner-aware `work` wrapper in assistant-home
- includes active task digest + local route suggestion
- launches the planner session unless the underlying wrapper is changed

### Use when
- the human wants the flexible default entrypoint
- route is not yet fully known
- planner supervision is desired

### Example
```bash
ygg work "fix theme selector on my site"
```

---

## `ygg explain`

### Purpose
Self-teaching vocabulary layer for Ygg verbs.

### v1 behavior
- explains what a verb does, when to use it, and examples
- supports:
  - `ygg explain` (lists known verbs)
  - `ygg explain <verb>` (full card)
  - `ygg explain --json` / `ygg explain <verb> --json`
- does not execute any work commands

### Use when
- you forgot a verb
- you want to keep command structure discoverable
- you want lightweight guidance without leaving the CLI

### Example
```bash
ygg explain
ygg explain suggest
ygg explain promote --json
```

---

## `ygg suggest`

### Purpose
Translate natural-language intent into candidate Ygg commands without executing them.

### v1 behavior
- interprets the request using the current router heuristics and active baton state
- prints a route interpretation (`action`, `confidence`, `reason`, and optional target)
- prints a **primary suggested command** plus a few good alternatives
- shows active tasks for context
- supports `--json` for machine-readable output
- supports optional `--domain` / `--task` hints to sharpen the command suggestions

### Use when
- you want help deciding what command to run next
- you want the system to carry more of the command-grammar burden
- you want natural language to compile into explicit structure before execution

### Example
```bash
ygg suggest "implement the improved theme selector UX"
ygg suggest --domain website-dev --task theme-selector-enhancements \
  "implement the improved theme selector UX"
```

---

## `ygg root`

### Purpose
Force direct entry into the planner spine with **no aggressive route guess**.

### v1 behavior
- builds a planner boot packet with forced route action `stay_in_planner`
- optional text is treated as context for the planner, not as a routing trigger
- launches planner by default
- can print the packet instead of launching

### Use when
- the human wants the control plane directly
- ambiguity is high
- planning should happen before delegation or lane switching

### Example
```bash
ygg root "help me decide the next move"
```

---

## `ygg branch`

### Purpose
Create or update a bounded task lane.

### v1 behavior
- wraps the current baton checkpoint mechanism
- creates/updates a domain + task baton pair
- sets or refreshes the active task for that domain
- accepts branch metadata such as objective, current state, next action, and locked decisions
- supports `--dry-run` for inspectability

### Required inputs
- `domain`
- `task`

### Optional metadata
- `--objective`
- `--current-state`
- `--next-action`
- `--status`
- `--priority`
- `--locked`
- `--rejected`
- `--reopen`
- `--artifact`
- `--agent`

### Use when
- work is separate from the current lane
- a human wants the branch to exist explicitly in baton state
- continuity should be inspectable from the filesystem

### Example
```bash
ygg branch website-dev theme-selector-enhancements \
  --objective "Add more functionality to the theme selector" \
  --next-action "Inspect current website implementation"
```

---

## `ygg resume`

### Purpose
Resume an existing lane with continuity context.

### v1 behavior
- wraps the current `resume open` mechanism
- opens a resume packet for a specified domain/task or, if there is exactly one active task overall, uses that automatically
- launches the target session by default
- supports `--print-only` to print the resume packet without launching
- supports semantic recall passthrough

### Inputs
- optional `domain`
- optional `task`

### Use when
- continuity is the main concern
- the human wants to reopen the right lane with hot working state

### Example
```bash
ygg resume website-dev theme-selector-enhancements
```

---

## `ygg forge`

### Purpose
Open the planner in an implementation/delegation posture for a specific lane.

### v1 behavior
- builds a planner boot packet with forced route action `suggest_spawn_codex`
- targets a specific active task or the sole active task if there is only one
- optional request text is included as implementation context
- launches planner by default
- supports `--print-packet`

### Important limitation in v1
`forge` does **not** directly spawn a coding agent by itself yet.
It prepares the planner with a strong implementation/delegation route suggestion.

### Use when
- the next move is implementation
- you want planner oversight but with coding/delegation bias

### Example
```bash
ygg forge --domain website-dev --task theme-selector-enhancements \
  "implement the improved theme selector UX"
```

---

## `ygg promote`

### Purpose
Make branch outcomes explicit instead of letting them disappear silently.

### v1 behavior
- records a promotion/disposition event to Ygg-local logs
- supports one of these dispositions:
  - `no-promote`
  - `log-daily`
  - `promote-durable`
  - `escalate-hitl`
- optional `--finish` marks the task done in baton state
- optional artifacts and note are preserved in the promotion record
- supports `--dry-run`

### Important limitation in v1
`promote-durable` does **not** automatically rewrite canonical long-term memory or policy surfaces.
In v1 it creates an explicit durable-promotion record so the outcome is inspectable and can be reviewed intentionally.

### Use when
- a branch produced a meaningful result
- you want an explicit fate for that result
- you want a durable trace of what happened next

### Example
```bash
ygg promote website-dev theme-selector-enhancements \
  --disposition log-daily \
  --note "Theme selector scope clarified and ready for build"
```

---

## `ygg status`

### Purpose
Inspect tracked baton state.

### v1 behavior
- wraps `resume status`
- shows domains, active task, freshness, and next action

### Use when
- you want to see what is active
- you want to choose the correct resume target
- you want a quick state sanity check

### Example
```bash
ygg status
ygg status website-dev
```

---

## v1 summary

The initial Ygg command family is about:

- translating natural language into explicit candidate commands,
- entering the spine clearly,
- creating branches explicitly,
- resuming the correct lane,
- biasing toward implementation when appropriate,
- and recording explicit promotion outcomes.

It is **not yet** a full autonomous orchestration layer.
That comes later if the current structure proves useful.
