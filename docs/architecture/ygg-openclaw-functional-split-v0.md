# Ygg × OpenClaw × Sandy Chaos — Functional Split v0

**Date:** 2026-04-03
**Status:** working architecture definition
**Intent:** prevent Ygg from being conceptually absorbed by OpenClaw, while preserving current runtime usefulness and forward portability

---

## Why this note exists

There is a real architectural drift risk:

- good Ygg ideas get implemented inside `.openclaw`
- those implementations become convenient
- convenience starts masquerading as ontology
- and eventually OpenClaw looks like the system, while Ygg gets reduced to a theme, naming layer, or afterthought

That is the wrong direction.

This note establishes the intended functional split clearly enough to guide shipping, refactoring, and future packaging.

---

## Core decision

**Ygg should be the thing that controls and defines continuity/orchestration behavior.**
**OpenClaw should be the runtime host/substrate that can instantiate and operate Ygg.**
**Sandy Chaos should remain the research/model/meaning engine that informs Ygg evolution.**

Short version:

- **Ygg = control plane / continuity system**
- **OpenClaw = runtime host / agent substrate**
- **Sandy Chaos = research and modeling engine**

This is the cleanest functional definition currently available.

---

## Functional roles

## 1) Ygg

### Ygg is:
- the canonical continuity/control plane
- the owner of identity continuity and orchestration semantics
- the home of wake/re-entry logic
- the authority on active work, event semantics, promotion stages, and branch/backflow rules
- the thing that should be portable and bootstrappable across Linux installs, sessions, hosts, and embodiments

### Ygg is not:
- just a skin/theme layered over OpenClaw
- just a collection of poetic docs
- just a channel/project naming scheme
- merely the current `.openclaw` workspace state

### Ygg should ultimately own:
- continuity kernel contracts
- active-work model
- event taxonomy
- promotion pipeline semantics
- memory utilization service interfaces
- branch/adapter rules
- packaging/install assumptions for its own stack

---

## 2) OpenClaw

### OpenClaw is:
- the runtime host
- the agent execution substrate
- the tool and session environment
- the interaction engine across channels/devices/surfaces
- the thing currently providing the live embodiment in which Ygg is being exercised

### OpenClaw is not:
- the canonical source of Ygg’s identity or doctrine
- the permanent conceptual home of Ygg architecture
- the final authority on continuity semantics

### OpenClaw should provide:
- execution/runtime capabilities
- session orchestration primitives
- tool access
- messaging/browser/device interfaces
- config and service host infrastructure

### Relation to Ygg
OpenClaw should be able to **host Ygg**.
It should not define Ygg’s entire ontology.

---

## 3) Sandy Chaos

### Sandy Chaos is:
- the research/model/meaning engine
- the place for theory-building, simulation, pressure-testing, concept refinement, and experimental formalization
- the source of many candidate ideas that may later inform Ygg

### Sandy Chaos is not:
- the canonical control plane
- the final operational authority for continuity state
- the permanent home for Ygg doctrine

### Sandy Chaos should own:
- research notes
- simulation specs
- concept packets
- falsification and benchmark artifacts
- model-development workflows
- retrieval/memory experiments before promotion into Ygg-facing systems

### Relation to Ygg
Sandy Chaos should **inform** Ygg, not replace it.

---

## The current reality vs the intended architecture

## Current reality
At present, a significant amount of live Ygg continuity work is happening under:

- `/home/ian/.openclaw/workspace-claw-main`

This includes:
- continuity doctrine
- kernel state surfaces
- active-work state
- event queues
- promotion queues
- session-level operational memory

That is acceptable as a **current embodiment/proving ground**.

## Intended architecture
However, the intended long-term architecture is:

- **Ygg repo/home** = canonical control-plane definition and portable system
- **OpenClaw workspace/runtime** = current embodiment host and operational substrate
- **Sandy Chaos repo** = research/model engine feeding future Ygg capabilities

This distinction must remain explicit.

---

## Canonical authority model

## Canonical Ygg authority should live in Ygg-owned surfaces

Preferred center of gravity:
- Ygg repo docs
- Ygg schemas/contracts
- Ygg packaging/install surfaces
- Ygg-defined service interfaces

## Runtime embodiment authority may temporarily live in OpenClaw-managed surfaces

Examples:
- current live kernel state files
- current session-bound active-work state
- current event traces
- current promotion traces

## Research authority should live in Sandy Chaos

Examples:
- memory-utilization benchmark design
- retrieval experiments
- concept formalization
- simulation plans
- theory pressure tests

---

## Practical rule for near-term shipping

Use this simple rule:

> **If the artifact defines what Ygg fundamentally is, it belongs in Ygg.**
> **If it records Ygg’s current live embodiment inside the running system, it may live in OpenClaw.**
> **If it explores or pressure-tests candidate capabilities, it belongs in Sandy Chaos.**

This rule should prevent most routing mistakes.

---

## What belongs where

## Put in Ygg
Artifacts about:
- functional definition
- architecture boundaries
- continuity kernel contracts
- active-work semantics
- event/promotion semantics
- packaging/install model
- branch/backflow rules
- service interfaces

## Put in OpenClaw workspace
Artifacts about:
- live embodiment state
- current session/runtime state
- local operator workflow for the running instance
- active event logs and current promotion queues
- temporary proving-ground implementations of Ygg services

## Put in Sandy Chaos
Artifacts about:
- modeling ideas
- retrieval experiments
- benchmark design
- concept pressure tests
- simulations
- theoretical synthesis
- candidate capability proposals before operational promotion

---

## Implications for current memory-utilization work

The memory-utilization effort should be split like this:

### In Sandy Chaos
- benchmark query artifacts
- evaluation notes
- retrieval-policy experiments
- concept and plan notes

### In Ygg
- canonical statement that memory utilization is a service above the continuity kernel
- canonical interface/contract expectations for derived memory surfaces

### In OpenClaw runtime surfaces
- current live implementation outputs such as:
  - `state/active-memory-index.json`
  - `state/recent-summary.json`
  - related derived caches

This is exactly the kind of split that preserves portability.

---

## Portability / bootstrappability stance

If Ygg is meant to become a portable installable system on Linux, then:

### Ygg must be able to boot with:
- its own doctrine
- its own schemas/contracts
- selective imported durable memory
- minimal empty runtime state
- adapter configuration

### Ygg must not require:
- one specific `.openclaw` directory layout as ontology
- one machine’s local history as identity
- one host’s runtime residue to understand itself

### OpenClaw should be treated as:
- one important and powerful host environment for Ygg
- but not the definition of Ygg itself

---

## Anti-drift guardrails

### Guardrail 1 — No ontology by convenience
Just because something was first implemented under `.openclaw` does not mean it belongs there canonically.

### Guardrail 2 — No accidental authority transfer
Runtime-local files should not silently become the only source of architectural truth.

### Guardrail 3 — No research burial
Sandy Chaos research should not get trapped in runtime glue before promotion decisions are made.

### Guardrail 4 — No kernel bloat
Ygg’s continuity kernel should stay narrow even if OpenClaw makes more expansive behavior easy.

### Guardrail 5 — Explicit backflow
Durable insights from runtime experiments and Sandy Chaos research must be promoted back into Ygg-owned doctrine/contracts when they become defining.

---

## Current recommended shipping posture

### Ship now
It is acceptable to continue shipping useful live work in the current OpenClaw embodiment.

### But keep definition clear
When something becomes:
- a statement of Ygg’s essence,
- a stable contract,
- or a packaging/install assumption,

it should be written in Ygg-owned surfaces.

### Therefore
This note is placed in the Ygg repo intentionally.

---

## Near-term migration stance

Do **not** attempt a giant migration all at once.

Instead:

1. keep current OpenClaw-hosted Ygg runtime useful
2. continue research/prototyping in Sandy Chaos
3. progressively extract canonical Ygg definitions/contracts into Ygg-owned docs and schemas
4. later package the portable pieces cleanly

This is a controlled extraction model, not a hard reset.

---

## Claim tiers

### Defensible now
- There is a real risk that Ygg ideas get absorbed into `.openclaw` by convenience.
- A clear functional split improves routing, portability, and conceptual sanity.
- Ygg should be treated as the continuity/control plane, OpenClaw as runtime host, and Sandy Chaos as research/model engine.

### Plausible but unproven
- This split will materially improve long-term packaging and installability.
- It will reduce architectural confusion and make promotion/extraction decisions easier.

### Speculative
- This functional split may become the basis of a broadly reusable system architecture beyond the current environment.

---

## Failure conditions

This framing fails if:
- Ygg never gains real ownership of its contracts and remains mostly branding,
- OpenClaw-local runtime residue continues to dominate architectural truth,
- Sandy Chaos research still gets operationally buried before promotion,
- or the split becomes rhetorical instead of changing routing and packaging behavior.

---

## Working rule to remember

> **Ygg defines. OpenClaw runs. Sandy Chaos discovers.**

That is the intended stack.
