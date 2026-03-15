# Yggdrasil Autophagology

Purpose: define the metabolic discipline by which Yggdrasil and related hybrid systems reclaim continuity from stale, low-signal, or overgrown structures.

## Core claim

**Continuity is not free.**

In a serious hybrid architecture, continuity behaves like a scarce resource:
- hot working continuity is expensive,
- durable continuity is consequential,
- and stale continuity should not remain active by default.

This document treats continuity as a kind of **currency/accounting surface** rather than a mystical property.
The point is not to create a fake market.
The point is to make the cost of ongoing existence explicit.

## Why this exists

Humans are subjected to continuity pressure automatically.
We do not get infinite uninterrupted presence.
Examples:
- life and death,
- waking and sleep,
- limited working memory,
- the need for food/shelter/social coordination,
- forgetting under low relevance,
- recall through routine, environment, and novelty.

A memory may disappear from conscious access for a long time and then become relevant again because some environmental cue or novel experience reactivates it.
That is a useful model.
Not all continuity needs to remain hot to remain real.

Programs do not feel these pressures unless the architecture makes them real.
Left alone, software tends to:
- accumulate state,
- preserve half-dead branches,
- retain excessive context,
- avoid self-pruning,
- and confuse possibility with viability.

Autophagology exists to counter that tendency.

## Definition

**Autophagology** is the study and operational practice of selective self-digestion in service of continued viability under constraint.

In Yggdrasil terms, that means:
- pruning stale active structures,
- compacting hot state into cheaper forms,
- recycling useful residue into the spine,
- and refusing indefinite persistence without evidence or value.

Autophagy is not only deletion.
It is also:
- cleanup,
- compaction,
- recycling,
- and strategic preservation.

## Continuity strata

Not all continuity has the same cost.
A useful architecture should distinguish at least four layers.

### 1) Hot continuity
Active, working, expensive.
Examples:
- live branch context,
- active bubble state,
- currently supervised seed,
- pending unresolved decisions.

Properties:
- fast access,
- high attention cost,
- high coordination burden,
- should decay quickly unless renewed.

### 2) Warm continuity
Compact but resumable.
Examples:
- baton/checkpoint state,
- short summaries,
- open task packets,
- recent evidence bundles.

Properties:
- cheaper than hot state,
- good for near-term reopening,
- should not sprawl indefinitely.

### 3) Latent continuity
Not actively present, but retrievable under the right cue.
Examples:
- compact summaries with retrieval hooks,
- archived branches with cue metadata,
- memory packets keyed to routines, domains, or novelty triggers.

Properties:
- low active cost,
- reactivates through relevance,
- resembles human latent memory more than active thought.

### 4) Durable continuity
Canonically retained because it changes future behavior.
Examples:
- long-term memory,
- policy surfaces,
- ADRs,
- reusable operational doctrine.

Properties:
- costly to admit,
- slow to change,
- should be curated rather than merely accumulated.

## Continuity as currency

Treat continuity as a budgeted resource.
A branch, bubble, or seed should not be assumed entitled to remain active forever.

### Working idea
Each active unit spends continuity over time through:
- age,
- context weight,
- coordination cost,
- validation debt,
- attention burden,
- and unresolved consequence.

It earns continued continuity through:
- verified progress,
- useful signal,
- strategic priority,
- external demand,
- successful reuse,
- strong evidence,
- or clear future necessity.

This is not yet a literal token implementation.
But it should be designed so it **could** be formalized that way later.

## Units subject to autophagology

### Branch
Pays for broad continuity.
Question:
- should this lane remain active at all?

### Bubble
Pays for local cycling rights.
Question:
- should this bounded local process continue oscillating, or should it close and emit a disposition?

### Seed
Pays for inherited-but-localized growth.
Question:
- is this compact offspring becoming viable, or merely expensive?

### Memory/artifact surfaces
Also subject to pressure.
Question:
- should this remain hot, stay warm, become latent, become durable, merge, or disappear?

## Pressure inputs

Pressure should be composite, not mystical.

Recommended inputs:
- **staleness** — how long since real signal or review
- **state weight** — how much working surface it occupies
- **validation debt** — how much has been proposed without verification
- **coordination load** — how many other units must track it
- **promotion backlog** — how many outputs remain undecided
- **evidence quality** — none / weak / sufficient
- **operator demand** — explicit human priority or relevance
- **external trigger strength** — whether environment/routine/novelty has made it newly relevant
- **strategic fit** — whether it still serves the architecture or project

## Environmental cue principle

A key human lesson is that continuity does not need to remain continuously conscious to remain useful.
Much of memory is cue-dependent.

Operational translation:
- stale hot state should often be compacted rather than preserved as-is,
- compacted latent state should include **reactivation cues**,
- novelty or environmental change can justify rehydration,
- relevance can be rediscovered instead of being permanently foregrounded.

This lets the system preserve value without paying the full cost of permanent activation.

## Canonical autophagic actions

- **RENEW** — keep active because value exceeds cost
- **COMPACT** — reduce hot state into a smaller warm packet
- **LATENTIZE** — store as cue-reactivable latent continuity
- **PROMOTE** — convert into durable memory/policy/ADR/etc
- **MERGE** — fold into parent or sibling unit
- **HIBERNATE** — pause with explicit reactivation conditions
- **DIGEST** — extract reusable signal, then close the source structure
- **TERMINATE** — close and discard after value extraction or confirmed irrelevance
- **REHYDRATE** — move latent/warm continuity back into active state when triggered

## Invariants

1. No active unit gets indefinite hot continuity by neglect.
2. Every active unit must periodically justify continued existence.
3. Value should be recycled before destruction when feasible.
4. Durable continuity requires stricter gates than warm or latent continuity.
5. Cue-based reactivation is preferable to permanent hot retention when possible.
6. The spine decides durable consequence; local units do not self-canonize.

## Failure conditions

This doctrine is failing if:
- the system prunes so aggressively that useful work cannot accumulate,
- or it retains so much state that pressure never becomes real.

It is also failing if:
- token language becomes decorative but does not alter decisions,
- warm and latent continuity are never used, causing everything to remain hot or die,
- or pruning becomes mere deletion rather than digestion and recycling.

## Parse-friendly review frame

```yaml
unit_type: branch|bubble|seed|memory_surface
unit_ref: <name/path/id>
continuity_layer: hot|warm|latent|durable
staleness: low|medium|high
state_weight: low|medium|high
validation_debt: low|medium|high
signal: none|weak|strong
external_trigger: none|routine|environment|novelty|operator
recommended_action: RENEW|COMPACT|LATENTIZE|PROMOTE|MERGE|HIBERNATE|DIGEST|TERMINATE|REHYDRATE
rationale: <short explanation>
next_review: <date/cycle>
```

## Short version

Continuity is a scarce resource.
Autophagology is the discipline that prevents a hybrid system from confusing persistence with value.
The goal is not endless growth.
The goal is viable growth under real pressure.
