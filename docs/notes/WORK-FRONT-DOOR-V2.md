# ygg work — Front Door V2

Status: draft
Owner: Ian + Claw

## Purpose

Define the next command-surface contract for `ygg work`.

The goal is to make `ygg work` the single default front door into Ygg continuity and planner flows without forcing qualifiers, while still preserving:
- deterministic underlying semantics
- inspectable routing
- bounded natural-language resolution
- explicit degradation behavior

This is a **spec draft**, not yet a live implementation guarantee.

---

## Design stance

### Defensible now
- `ygg work` should be the easiest default entrypoint.
- Qualifiers should sharpen routing, not be required for useful behavior.
- Natural language should act as a **soft resolver layer** over a deterministic core, not replace command grammar.
- The command should consume explicit state surfaces before inventing summary prose.

### Plausible but unproven
- Reading both task state and concept/tension/pressure state will improve startup briefs and reduce branch/spine drift.
- A single strong front door will outperform a growing family of nearly-duplicate entry verbs.

### Speculative
- Over time, `ygg work` could become the primary command for most human entry while other verbs remain available as explicit low-level controls.

---

## Core rule

`ygg work` should behave like:

> **one command, deterministic core, optional language softness**

This should be the main human-facing rule of the command surface.
Other verbs may remain important, but mainly as:
- explicit controls
- programmable route targets
- debugging/inspection surfaces
- machine-oriented subroutines behind the front door

That means:
- the human can type `ygg work`
- or `ygg work <qualifier>`
- or `ygg work "<natural-language intent>"`
- but internally the system still resolves into a structured execution packet

The structured packet should at minimum resolve:
- continuity target
- working root
- session / mode
- startup brief payload
- confidence / degradation posture

---

## Default behavior

## `ygg work`

With no qualifiers, `ygg work` should:

1. resolve the active continuity target
2. read the most relevant continuity surfaces
3. produce one startup brief
4. enter the planner/front-door session with that brief

### Required state inputs

The default resolution path should consult, in order of authority:

1. active task baton / resume state
2. `state/active-work.json`
3. `state/concept-spine.json`

### Why this order

- baton state captures the hottest local lane/task continuity
- active-work captures the broader current operational picture
- concept-spine captures concept/tension/pressure context that task-only state misses

### Startup brief should include

- resolved domain/task
- continuity quality (`live`, `degraded`, or equivalent)
- likely mission
- next action
- active concept summary
- open tension summary
- active pressure summary
- disposition/promotion relevance when present

---

## Qualifiers

Qualifiers should remain available, but optional.

### Acceptable qualifier classes

#### 1. Explicit target qualifiers
Examples:
- `ygg work ygg-dev`
- `ygg work sandy-chaos-alignment-constraints-v1`
- `ygg work ygg-dev sandy-chaos-alignment-constraints-v1`

Use these when the human wants an exact lane/task target.

#### 2. Mode qualifiers
Examples:
- `ygg work --mode planner`
- `ygg work --mode implementation`
- `ygg work --mode review`

Use these when the human wants to bias the posture while preserving the same entry command.

#### 3. Intent qualifiers via natural language
Examples:
- `ygg work "continue the Sandy Chaos constraints lane"`
- `ygg work "implementation mode for the active lane"`
- `ygg work "resume Ygg architecture planning"`

Use these when the human wants the command to resolve ambiguity softly.

---

## NLP as soft resolver layer

## Rule

Natural language should be allowed to influence routing, but not define the core semantics.

### Meaning in practice

NLP may help infer:
- likely domain/task target
- likely mode (`planner`, `implementation`, `review`)
- whether the user wants continuation vs fresh routing

But NLP should not bypass:
- explicit continuity resolution
- baton/active-work/concept-spine reads
- ambiguity checks
- degraded-state disclosure

## Good pattern

Natural language compiles into a structured interpretation such as:

```json
{
  "target": {
    "domain": "ygg-dev",
    "task": "sandy-chaos-alignment-constraints-v1"
  },
  "mode": "planner",
  "intentClass": "continue-active-lane",
  "confidence": 0.84,
  "degraded": false
}
```

## Bad pattern

Treating natural language as a magical source of authority that silently selects a lane/mode with no visible resolution logic.

---

## Consumption of `state/concept-spine.json`

`ygg work` should treat `state/concept-spine.json` as an advisory continuity surface.

It should use it to improve:
- startup brief quality
- concept-level resumability
- pressure visibility
- branch/spine routing hints

It should **not** treat concept-spine as authoritative for:
- direct policy mutation
- runtime mutation by itself
- command execution without other continuity checks

## Minimum useful extraction

From concept-spine, `ygg work` should at minimum be able to render:
- focus concept
- open tension
- active pressure
- promotion/disposition hint

Example brief fragment:

- focus concept: Ygg concept-governance control surface
- open tension: task-only resumability is insufficient for concept-governance work
- active pressure: need first inspectable concept/tension/pressure state surface
- disposition: TODO_PROMOTE

---

## Resolution order (proposed)

### Phase A — explicit input resolution
1. If explicit domain/task args are present, prefer them.
2. Else if exactly one hot active task exists, prefer that.
3. Else consult soft resolver/NLP for likely target.
4. If still ambiguous, stay in planner and say so.

### Phase B — continuity assembly
1. read baton/resume state
2. read `state/active-work.json`
3. read `state/concept-spine.json` if present
4. mark continuity quality as `live` / `partial` / `degraded`

### Phase C — brief generation
Generate one startup brief with:
- target
- mission
- next move
- concept/tension/pressure layer
- explicit degradation note if needed

### Phase D — mode routing
If the user asked for a mode explicitly or NLP confidence is high enough, add that posture to the launch packet.
Otherwise default to planner mode.

---

## Failure behavior

If resolution is degraded, `ygg work` should say so plainly.

Examples:
- multiple active tasks; entering planner without lane lock
- no concept-spine present; using task-only continuity
- stale baton state; startup brief may be partial

The command should never pretend full continuity when only fallback continuity exists.

---

## Non-goals

Not part of this draft:
- replacing `ygg resume`
- removing explicit verbs
- freeform agentic execution from raw prose
- broad ontology inference
- hidden planner heuristics with no inspectable output
- turning every explicit verb into a mandatory human-facing command the user must remember

`ygg work` should be the **best front door**, not the only door.
The rest of the surface should increasingly feel like a stable internal toolkit that humans can still reach when they want precision.

---

## Recommended implementation sequence

1. keep `ygg work` as the default front door
2. update its contract/docs first
3. add structured resolution logic for baton + active-work + concept-spine
4. add optional mode qualifiers
5. add NLP soft resolution
6. test ambiguity/degradation cases before calling the behavior stable

---

## Acceptance criteria

This draft succeeds if future implementation yields a `ygg work` that:
- works well with no qualifiers
- accepts explicit qualifiers cleanly
- allows natural language without losing inspectability
- consumes `state/concept-spine.json` usefully
- surfaces degraded continuity honestly
- improves startup brief quality without multiplying verbs
