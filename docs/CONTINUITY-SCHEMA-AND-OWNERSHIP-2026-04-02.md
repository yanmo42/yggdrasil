# Continuity Schema + Ownership Map — 2026-04-02

## Purpose

Define the next-layer canonical model for Ygg continuity so the repo can integrate:

- the existing semantic checkpoint kernel in `~/ygg`
- the new runtime-continuity work from assistant-home (Heimdall / Ratatoskr)
- the missing structured inventory for **ideas** and **active programs**

This document is the design target for the next implementation pass.

---

## Design stance

Use the architecture we already have.
Do **not** invent a parallel continuity stack.

Build on:
- `lib/ygg/continuity.py`
- `state/ygg/checkpoints/`
- `ygg checkpoint`
- `ygg promote --lane ...`
- `ygg status --continuity`

Add the missing structured state around that kernel.

---

## Canonical ownership split

## 1. Ygg-owned semantic continuity state

This belongs in `~/ygg`.
It is part of the product/control-plane layer.

### Canonical path family
- `~/ygg/state/ygg/`

### Artifact classes
- continuity checkpoints
- active programs registry
- ideas registry
- topology/relationship metadata (optional, later)
- promotion candidates / semantic outcomes

### Why Ygg owns this
- this is control-plane meaning, not just local runtime noise
- it should be inspectable, portable, and releaseable with Ygg
- it should not depend on one specific assistant-home chat session to exist

---

## 2. Ygg-owned runtime continuity infrastructure

This also belongs in `~/ygg`, but conceptually separate from semantic state.

### Canonical module family
Suggested target:
- `~/ygg/lib/ygg/continuity_runtime.py`
- or
- `~/ygg/lib/ygg/continuity/heimdall.py`
- `~/ygg/lib/ygg/continuity/ratatoskr.py`

### Artifact classes
- runtime embodiment refresh
- change detection / fingerprinting
- continuity event routing
- sink adapters for notes / promotion / stdout / future bridges

### Why Ygg owns this
- it is general continuity machinery
- it should be inspectable and testable as part of Ygg proper
- assistant-home should consume/invoke it, not be its only home

---

## 3. Assistant-home-owned local memory + embodiment state

This stays outside Ygg repo canon.

### Current surfaces
- `~/.openclaw/workspace-claw-main/core/MEMORY.md`
- `~/.openclaw/workspace-claw-main/memory/daily/*`
- `~/.openclaw/workspace-claw-main/state/ygg-self.json` (current live form)
- persona/runtime local files

### Why assistant-home owns this
- it is personal/local runtime continuity
- it may contain local-only machine/session facts
- it is not the same thing as Ygg’s portable semantic control-plane state

### Important note
Ygg may define the **schema/template/adapter** for runtime self state, but should not commit one machine’s live snapshot as canonical repo truth.

---

## Canonical state model

## A. Existing kernel: checkpoints

Path:
- `state/ygg/checkpoints/*.json`

Current role:
- append-only semantic continuity decision records
- one bounded lane/outcome per artifact

Keep this.
Do not replace it.

### Current shape
```json
{
  "timestamp": "2026-03-27T21:41:12.361720+00:00",
  "lane": "topological-memory",
  "summary": "Ratified bounded research direction: topology-aware continuity retrieval over the current ecosystem",
  "disposition": "TODO_PROMOTE",
  "promotion_target": "docs/archive/topological_memory_continuity_retrieval_v0.md",
  "evidence": "Concept origin: Ian (2026-03-27); developed with Solace/Nyx; benchmark-first bounded framing established",
  "next_action": "Build 30-query benchmark against keyword, recency, and embedding baselines"
}
```

### Role in the larger model
Checkpoints are the durable event ledger.
They should stay the smallest common denominator for:
- what changed
- why it matters
- what happens next

---

## B. New file: programs registry

### Canonical path
- `~/ygg/state/ygg/programs.json`

### Purpose
Track the current higher-level active programs/lanes that matter across time.
This is broader than a single checkpoint and more semantic than baton state.

### What counts as a program
Examples:
- Ygg continuity integration
- Sandy Chaos research kernel
- site/app interface work
- memory retrieval benchmark work
- release/productization work

A program is:
- durable enough to matter over multiple sessions
- concrete enough to have status and next action
- broader than one isolated checkpoint

### Suggested schema
```json
{
  "version": 1,
  "updatedAt": "2026-04-02T14:30:00-04:00",
  "programs": [
    {
      "id": "ygg-continuity-integration",
      "title": "Ygg continuity integration",
      "status": "active",
      "kind": "productization",
      "summary": "Integrate semantic continuity kernel with runtime continuity machinery and prepare Ygg for release.",
      "owner": "ian+ygg",
      "priority": "high",
      "relatedLanes": ["continuity", "topological-memory"],
      "artifacts": [
        "docs/OPENCLAW-INTEGRATION-AUDIT-2026-04-02.md",
        "docs/CONTINUITY-SCHEMA-AND-OWNERSHIP-2026-04-02.md"
      ],
      "nextAction": "Promote Heimdall/Ratatoskr into ~/ygg and define programs/ideas schema wiring.",
      "updatedFrom": "manual|checkpoint|ratatoskr",
      "notes": []
    }
  ]
}
```

### Status vocabulary
Keep minimal:
- `active`
- `watching`
- `blocked`
- `hibernating`
- `completed`
- `dropped`

### Ownership rule
This file is **semantic registry state**, not chat memory.
It belongs in Ygg.

---

## C. New file: ideas registry

### Canonical path
- `~/ygg/state/ygg/ideas.json`

### Purpose
Track durable ideas that are not yet programs, or that may feed programs later.
This is the parking garden for concepts that are worth preserving without pretending they are active execution lanes.

### Suggested schema
```json
{
  "version": 1,
  "updatedAt": "2026-04-02T14:30:00-04:00",
  "ideas": [
    {
      "id": "topology-aware-continuity-retrieval",
      "title": "Topology-aware continuity retrieval",
      "status": "incubating",
      "summary": "Use topology-aware retrieval over the current ecosystem instead of flat memory recall.",
      "claimTier": "plausible",
      "origin": "Ian + Solace/Nyx",
      "links": {
        "checkpoints": [
          "state/ygg/checkpoints/2026-03-27T21-41-12.361720+00-00_topological-memory.json"
        ],
        "promotionTargets": [
          "docs/archive/topological_memory_continuity_retrieval_v0.md"
        ],
        "programs": []
      },
      "nextAction": "Build 30-query benchmark against keyword, recency, and embedding baselines",
      "tags": ["memory", "retrieval", "topology"],
      "notes": []
    }
  ]
}
```

### Status vocabulary
Keep minimal:
- `incubating`
- `testing`
- `parked`
- `adopted`
- `rejected`

### Ownership rule
This file is Ygg semantic state.
Not assistant-home memory.

---

## D. Optional later file: topology

### Canonical path
- `~/ygg/state/ygg/topology.json`

### Purpose
Express relationships between:
- ideas
- programs
- checkpoints
- maybe branch/lane families later

### Not required for immediate implementation
Do **not** start here.
Add only if programs/ideas files make a clear need obvious.

### Likely role later
- parent/child relationships
- reinforces / blocks / depends-on links
- branch clusters or project maps

For now, simple embedded references are enough.

---

## Runtime embodiment state model

## E. Runtime self snapshot template

### Canonical status
This is real and useful, but should be treated as **runtime-generated local state**, not semantic registry state.

### Repo-owned pieces
Ygg should own:
- schema/template/example
- refresh logic (Heimdall)
- event routing hooks (Ratatoskr)

### Suggested repo-safe artifact
- `~/ygg/state/templates/ygg-self.example.json`

### Suggested runtime artifact
- `~/ygg/state/runtime/ygg-self.json`
  or
- assistant-home local equivalent via adapter

### Top-level shape
```json
{
  "identity": {},
  "continuity": {},
  "platformDefaults": {},
  "runtimeSnapshot": {},
  "runtimeHistory": {}
}
```

### Ownership rule
- schema/template: Ygg-owned
- live snapshot: local runtime state

---

## Integration rules

## 1. Heimdall does **not** own ideas/programs

Heimdall should:
- inspect runtime embodiment
- compute fingerprint/diff
- update runtime self snapshot
- emit a structured event when meaningful change occurs

Heimdall should **not**:
- decide semantic program status
- mutate ideas registry directly
- become a general continuity brain

---

## 2. Ratatoskr may bridge runtime events into semantic artifacts, but only carefully

Ratatoskr should:
- route structured events to configured sinks
- support note/promotion/checkpoint sinks
- optionally create continuity checkpoints when event significance is high and rules allow it

Ratatoskr should **not**:
- spam daily memory by default
- infer durable ideas automatically from weak signals
- rewrite semantic registries without explicit rules

### Good first integration
Ratatoskr may write:
- a checkpoint into `state/ygg/checkpoints/` for important runtime changes
- a Ygg-local note artifact
- assistant-home daily note only through an explicit adapter/sink

---

## 3. Checkpoints are the bridge between runtime and semantic state

Best rule:
- runtime changes become events
- important events may become checkpoints
- programs and ideas may reference checkpoints
- programs and ideas are not raw event logs

This avoids stuffing low-level runtime noise into semantic registries.

---

## 4. Programs and ideas should be updated deliberately

Preferred sources:
- explicit operator edits
- explicit commands
- bounded promotion/checkpoint logic

Avoid:
- automatic mutation from every session twitch
- hidden heuristics changing core semantic state without visibility

---

## Initial command/implementation implications

## Keep existing commands
- `ygg checkpoint`
- `ygg promote --lane ...`
- `ygg status --continuity`

## Likely next commands later
Not necessarily now, but this is the likely trajectory:
- `ygg programs list`
- `ygg programs set ...`
- `ygg ideas list`
- `ygg ideas add ...`
- `ygg ideas promote ...`

Do not add all of these immediately unless needed.
First get the data model and file ownership right.

---

## Recommended implementation order

### Phase 2A — promote runtime continuity machinery into Ygg
1. move Heimdall logic into `~/ygg/lib/ygg/...`
2. move Ratatoskr logic into `~/ygg/lib/ygg/...`
3. remove assistant-home-only imports
4. create portable sink adapters

### Phase 2B — add repo-safe runtime self template
5. add `state/templates/ygg-self.example.json`
6. document runtime output location under `state/runtime/`

### Phase 2C — extend semantic continuity kernel
7. add `state/ygg/programs.json` schema
8. add `state/ygg/ideas.json` schema
9. document how checkpoints reference programs/ideas

### Phase 2D — wire minimal integration
10. allow Ratatoskr to emit Ygg-local checkpoint artifacts
11. keep assistant-home daily memory as optional adapter only

---

## Concrete ownership summary

### Ygg repo canonical
- `lib/ygg/continuity.py`
- future Heimdall/Ratatoskr runtime modules
- `state/ygg/checkpoints/`
- `state/ygg/programs.json`
- `state/ygg/ideas.json`
- repo docs/contracts/templates

### Assistant-home local only
- `core/MEMORY.md`
- daily memory files
- live local runtime snapshot
- persona/relationship files

### Bridge surfaces
- adapters from Ygg runtime events into assistant-home daily memory
- explicit docs for OpenClaw invocation/integration
- optional sync logic, never hidden ownership blur

---

## Bottom line

The canonical model should be:

- **checkpoints** = event ledger
- **programs** = active durable work inventory
- **ideas** = incubating concept inventory
- **runtime self snapshot** = local embodiment state
- **Heimdall/Ratatoskr** = runtime continuity machinery and routing, not the semantic registry itself

That gives Ygg a clean releaseable core without collapsing semantic continuity and local runtime embodiment into one blob.
