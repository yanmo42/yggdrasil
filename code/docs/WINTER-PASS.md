# Yggdrasil Winter Pass

Purpose: define the periodic pressure protocol that makes continuity cost real.

Builds on:
- `autophagology.md`
- `branch-contract.md`
- `promotion-gate.md`

## Core idea

A hybrid system should not rely on good intentions to prune itself.
It should periodically enter a review mode in which active structures must justify their continued claim on attention, context, and memory.

This protocol is called **Winter Pass**.

Winter is the season in which excess growth is tested.
The point is not punishment.
The point is viability.

## Trigger conditions

Run Winter Pass when any of the following are true:
- scheduled cadence arrives (daily / weekly / phase boundary)
- active branch count exceeds threshold
- hot-state/context load exceeds threshold
- promotion backlog exceeds threshold
- human requests a cleanup/pruning review
- major environment shift or project phase change occurs

## Scope

Winter Pass may evaluate:
- branches
- bubbles
- seeds
- warm checkpoints
- latent memory packets queued for deletion or reactivation
- unresolved outputs awaiting promotion/disposition

## Required question set

Each unit under review must answer:

1. **What value have you produced since last review?**
2. **What evidence supports your continued existence?**
3. **What is your current cost?**
4. **What continuity layer are you occupying?**
5. **What cues would justify future reactivation if you were compacted?**
6. **What should be recycled if you are closed?**
7. **What happens if you are terminated now?**

No answer is itself a signal.
Silence should count against continuation.

## Continuity economics

Winter Pass operationalizes a simple accounting rule:

- active continuity spends budget over time,
- evidence and usefulness renew budget,
- stale unresolved structures lose budget,
- and low-signal units should be compacted, latentized, digested, or terminated.

The system does not need a literal token ledger in v1.
But the decisions should be compatible with later tokenization.

## Review pipeline

### 1) Enumerate
Collect all in-scope units.
Include:
- unit type,
- current layer,
- last meaningful update,
- current owner/supervisor,
- current objective,
- outstanding obligations.

### 2) Measure pressure
Assess:
- staleness,
- state weight,
- validation debt,
- coordination load,
- promotion backlog,
- operator demand,
- external trigger strength.

### 3) Check signal
Ask whether the unit has:
- new evidence,
- verified progress,
- strong future relevance,
- or only inertia.

### 4) Check cue value
If the unit is not worth remaining hot, ask whether it is still worth preserving as warm or latent continuity.

Examples of good reactivation cues:
- repo/path/domain reference
- recurring routine or calendar event
- explicit human request class
- novelty condition
- dependency completion
- environment/state change

### 5) Choose disposition
Allowed dispositions:
- `RENEW`
- `COMPACT`
- `LATENTIZE`
- `PROMOTE`
- `MERGE`
- `HIBERNATE`
- `DIGEST`
- `TERMINATE`
- `ESCALATE_HITL`

### 6) Reclaim value
Before closing a unit, attempt to reclaim:
- evidence,
- summaries,
- reusable contracts,
- policy lessons,
- retrieval cues,
- and durable insights.

### 7) Write trace
Every Winter Pass decision should record:
- unit reviewed,
- pressure assessment,
- disposition,
- reclaimed artifacts,
- next review or closure marker.

## Disposition rubric (fast)

### `RENEW`
Use when:
- signal is strong,
- cost is acceptable,
- and active continuity is still justified.

### `COMPACT`
Use when:
- value remains,
- but hot form is too expensive.

### `LATENTIZE`
Use when:
- current relevance is low,
- but a future cue could make it valuable again.

### `PROMOTE`
Use when:
- the output should alter durable memory, policy, or architecture.

### `MERGE`
Use when:
- the unit should not survive independently,
- but its value belongs inside another lane.

### `HIBERNATE`
Use when:
- continuation may be justified later,
- but no current evidence supports active cost.

### `DIGEST`
Use when:
- the unit should end,
- but should first be reduced into reusable residue.

### `TERMINATE`
Use when:
- value is absent or exhausted,
- and preservation would only create drag.

### `ESCALATE_HITL`
Use when:
- the value/cost tradeoff is ambiguous,
- or termination/promotion would have high consequence.

## Suggested continuity layers after review

- `hot` -> active only when justified now
- `warm` -> compact, near-term, low-latency resume
- `latent` -> cue-reactivable, low-cost storage
- `durable` -> canonical, slow-changing, formally promoted
- `none` -> terminated after digestion or irrelevance

## Example mental model

Human cognition already works somewhat like this.
Not everything stays in working memory.
Some things remain routine.
Some fall dormant and reactivate only when a cue arrives.
Some become identity-shaping or durable memory.
Sleep itself is a periodic discontinuity that changes what remains active and what gets consolidated.

Winter Pass tries to give computational systems an analogous pressure regime instead of letting everything remain permanently summer.

## Guardrails

1. Do not prune without first asking whether compaction or latentization is better.
2. Do not preserve hot state merely because it already exists.
3. Do not promote durable continuity just to avoid making a pruning decision.
4. Do not allow unresolved units to accumulate without review.
5. Do not confuse nostalgia for a branch with evidence of value.

## Failure conditions

Winter Pass is failing if:
- everything gets renewed and nothing meaningful is reclaimed,
- or almost everything gets terminated and the architecture loses continuity.

It is also failing if:
- latent continuity is never rehydrated when cues return,
- review cadence is irregular enough that pressure becomes fictional,
- or records are too vague to explain why a unit survived or died.

## Parse-friendly pass record

```yaml
winter_pass_id: WINTER-YYYYMMDD-XX
unit_type: branch|bubble|seed|checkpoint|memory_surface
unit_ref: <name/path/id>
objective: <short description>
continuity_layer_before: hot|warm|latent|durable
staleness: low|medium|high
state_weight: low|medium|high
validation_debt: low|medium|high
signal: none|weak|strong
external_trigger: none|routine|environment|novelty|operator
disposition: RENEW|COMPACT|LATENTIZE|PROMOTE|MERGE|HIBERNATE|DIGEST|TERMINATE|ESCALATE_HITL
reclaimed_artifacts:
  - <path/ref>
next_state: hot|warm|latent|durable|none
next_review: <date/cycle>
notes: <short rationale>
```

## Short version

Winter Pass is how the architecture makes pressure real.
It turns continuity from an unlimited default into something that must be renewed, compacted, recycled, or released.
