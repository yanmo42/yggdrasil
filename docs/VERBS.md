# Verb Spec (Ygg v1)

This file defines what each `ygg` verb is supposed to do **before** implementation details drift.

## Design rule

The command family should be poetic in **topology, cadence, and consequence** while remaining clear in **action semantics**.

That means:

- the ontology may be symbolic (`spine`, `branch`, `promotion`)
- the verbs should still tell the truth about what they do

For the strict per-verb input/output/mutation guarantees, see `docs/CONTRACTS.md`.

---

## `ygg work`

### Purpose
The **default human entrypoint** into Ygg.

`ygg work` is where the human should be able to start most of the time.
The rest of the command family should increasingly behave like:
- explicit low-level controls
- inspectable escape hatches
- machine-callable routing targets
- debugging and contract surfaces

### Current behavior (v1 live)
- forwards to the current planner-aware `work` wrapper in assistant-home
- includes active task digest + local route suggestion
- launches the planner session unless the underlying wrapper is changed

### Draft next behavior (target)
- `ygg work` with no qualifiers should resolve the active continuity target and generate a startup brief
- should consume, in priority order:
  - active task baton / resume state
  - `state/active-work.json`
  - `state/concept-spine.json`
- should treat natural language as a **soft resolver layer** over a deterministic core
- should accept optional explicit qualifiers for target and mode without requiring them
- should surface degraded continuity honestly when resolution is partial or ambiguous
- should remain easy for humans while resolving into explicit structured packets internally

### Use when
- the human wants the default front door
- route is not yet fully known
- planner supervision is desired
- continuity should be assembled before deeper execution choices
- the user wants NLP convenience without surrendering inspectability

### Examples
```bash
ygg work
ygg work "fix theme selector on my site"
ygg work ygg-dev
ygg work "continue the Sandy Chaos constraints lane"
```

### Strategic note
The long-term shape should be:
- **human enters through `ygg work` most of the time**
- other verbs remain available because explicit control, scripting, predictability, and machine-to-machine routing still matter

### Note
See `docs/notes/WORK-FRONT-DOOR-V2.md` for the draft front-door contract and resolution order.

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
  - `ygg help` / `ygg help <verb>` as a direct alias
- includes contract details (mutability, required inputs, guarantees, failure conditions)
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

## `ygg frontier`

### Purpose
Audit the current Sandy Chaos research frontier so Ygg can expose foundations, evidence, proof debt, and the best next move.

### v0 prototype behavior
- supports:
  - `ygg frontier list`
  - `ygg frontier current`
  - `ygg frontier queue`
  - `ygg frontier sync`
  - `ygg frontier audit`
  - `ygg frontier open`
  - `ygg frontier audit --json`
- reads Sandy Chaos source surfaces in a read-only way
- resolves targets through the explicit registry at `state/ygg/frontiers.json`
- `ygg frontier sync` builds a queue of Ygg frontier candidates from assistant-home `state/resume/tasks/ygg-dev--*.md` batons.
- `ygg frontier queue` shows the synced queue, with one active frontier and the rest held as ready/waiting/blocked/done.
- `ygg frontier open` now prefers the queued active/ready Ygg frontier before falling back to the Sandy Chaos registry handoff path.
- first target in that registry is the current symbolic-maps discriminating-benchmark frontier

### Use when
- you want one compact readout of frontier rigor rather than only continuity state
- you need a source-explicit view of assumptions, evidence, missing nulls, and next move
- you want Ygg to help Sandy Chaos become more scientifically legible

### Example
```bash
ygg frontier list
ygg frontier current
ygg frontier queue
ygg frontier sync
ygg frontier audit
ygg frontier open
ygg frontier audit --json
```

---

## `ygg program`

### Purpose
Inspect the canonical semantic program registry.

### v1 behavior
- supports:
  - `ygg program list`
  - `ygg program list --json`
  - `ygg program show <id>`
  - `ygg program show <id> --json`
- reads `state/ygg/programs.json`
- does not mutate registry state

### Use when
- you want the durable work inventory in CLI form
- you need one exact program record by id

### Example
```bash
ygg program list
ygg program show ygg-continuity-integration
```

---

## `ygg idea`

### Purpose
Inspect the canonical semantic idea registry.

### v1 behavior
- supports:
  - `ygg idea list`
  - `ygg idea list --json`
  - `ygg idea show <id>`
  - `ygg idea show <id> --json`
- reads `state/ygg/ideas.json`
- does not mutate registry state

### Use when
- you want the incubating concept inventory in CLI form
- you need one exact idea record by id

### Example
```bash
ygg idea list
ygg idea show topology-aware-continuity-retrieval
```

---

## `ygg suggest`

### Purpose
Translate natural-language intent into candidate Ygg commands without executing them.

### v1 behavior
- interprets the request using the current router heuristics and active baton state
- prints a route interpretation (`action`, `confidence`, `reason`, and optional target)
- prints a **primary suggested command** plus a few good alternatives
- includes quick posture blurbs + `ygg help <verb>` contract pointers for each suggestion
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
- supports `--print-worker-command` to emit a ready-to-run Codex command instead of launching planner
- supports `--wake-now` to bake an immediate `openclaw system event --mode now` hook into the printed worker command

### Important limitation in v1
`forge` still does **not** directly spawn a coding agent by itself yet.
What it can do now is either:
- prepare the planner with a strong implementation/delegation route suggestion, or
- print the exact worker command you can run next.

### Design role
`forge` should be thought of less as a primary human front door and more as:
- an explicit execution-bias control
- a machine-callable internal route target
- a debugging/inspection surface when you want to see the exact implementation handoff posture

If the user is not sure what to run, the better answer should usually be `ygg work`, not `ygg forge`.

### Use when
- the next move is implementation
- you want planner oversight but with coding/delegation bias
- you need a precise, explicit execution-oriented control rather than the general front door

### Example
```bash
ygg forge --domain website-dev --task theme-selector-enhancements \
  "implement the improved theme selector UX"

# print the exact codex command with wake behavior baked in
ygg forge --domain ygg-dev --task sandy-chaos-alignment-constraints-v1 \
  --print-worker-command --wake-now
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

## `ygg mode`

### Purpose
Persist or inspect persona-mode override state for Solace/Nyx, with optional live session notification.

### v1 behavior
- `ygg mode nyx` persists a Nyx override and sends a switch directive to a target session by default
- `ygg mode solace` persists a Solace override and sends a switch directive to a target session by default
- `ygg mode get` prints the current override/effective mode
- `ygg mode clear` removes the manual override and returns control to automatic domain routing
- writes mode state to both Ygg runtime state and assistant-home workspace state for future startup reads
- supports `--no-notify` to persist without messaging a live session
- supports `--print-message` to print the directive text instead of sending it

### Use when
- you want Nyx or Solace to stay foregrounded beyond one prompt
- you want a small command-surface switch instead of conversational mode requests
- you want to return to automatic routing after a temporary override

### Examples
```bash
ygg mode nyx
ygg mode solace
ygg mode get
ygg mode clear
ygg mode nyx --session planner--main
ygg mode nyx --no-notify
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

## `ygg raven`

### Purpose
Run RAVENS v1 flight operations.

### v1 behavior
- `ygg raven launch ...` creates a flight artifact + event log entries
- `ygg raven status` lists known flights
- `ygg raven inspect <flight-id>` prints one flight artifact
- `ygg raven return <flight-id>` writes a structured return packet and marks the flight returned
- `ygg raven adjudicate <flight-id> <disposition>` records an explicit spine disposition on the flight

### Safety posture
- artifact scaffolding only
- no destructive execution
- no autonomous hard-beak actions

### Examples
```bash
ygg raven launch --trigger human-request "Inspect package boundary drift"
ygg raven status
ygg raven return <flight-id>
ygg raven adjudicate <flight-id> ADOPT
```

---

## `ygg graft`

### Purpose
Create additive structural growth proposals.

### v1 behavior
- `ygg graft propose ...` writes a `GRAFT-*.md` artifact under raven runtime state
- proposal only (no automatic application)

### Example
```bash
ygg graft propose "Add proposal gate" --target-attachment state/policy/
```

---

## `ygg beak`

### Purpose
Create subtractive/reshaping proposals for governance review.

### v1 behavior
- `ygg beak propose ...` writes a `BEAK-*.md` artifact
- defaults to soft beak class
- hard beaks are metadata/proposal only in v1

### Example
```bash
ygg beak propose "Deprecate duplicate docs" --target docs/ --problem-type duplication
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
