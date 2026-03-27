# RAVENS v1 — Roaming Cognition Specification

- Status: Draft
- Scope: Implementable v1 protocol
- Builds on:
  - `docs/RAVENS.md`
  - ADR-0002 (Yggdrasil architecture)
  - ADR-0003 (spine-first omnidirectional topology)
  - ADR-0004 (transcript spine access)

---

## 1. Purpose

RAVENS v1 defines a **governed roaming cognition subsystem** for Ygg.

It exists to let the system:
- leave the spine intentionally,
- inspect environment and system surfaces,
- gather evidence,
- form and compare interpretations,
- return with inspectable consequence,
- and propose structural change without bypassing governance.

The mythic language is intentional.
The implementation must remain **operational, observable, and reality-coupled**.

RAVENS is not a second root.
It is a roaming subsystem in service of the canonical spine.

---

## 2. Design goals

### Defensible now
1. Make scouting and return behavior explicit.
2. Make raven activity visible to the human operator.
3. Preserve spine authority over acceptance, rejection, and durable writes.
4. Support proposal-generation for self-improvement and environmental adaptation.
5. Distinguish additive change (**grafts**) from subtractive change (**beaks**).

### Plausible next
1. Let ravens confer in an isolated interaction zone.
2. Allow spine to route, compare, and selectively trust raven returns.
3. Let the operator inspect raven flights as first-class objects.

### Non-goals for v1
1. Fully autonomous self-rewriting.
2. Unbounded destructive edits.
3. Hidden background agents with no observable traces.
4. Replacing the spine with raven consensus.

---

## 3. Core ontology

## 3.1 Spine

The spine is the canonical control plane.

Responsibilities:
- commissions raven flights,
- defines scope and permissions,
- receives returns,
- adjudicates grafts and beaks,
- decides promotion class,
- preserves durable continuity.

The spine may use raven interaction history as decision input, but ravens do not overrule the spine.

## 3.2 Huginn

Huginn is **thought / outward scouting**.

Primary role:
- explore,
- inspect,
- search,
- hypothesize,
- compare options,
- identify possible grafts or structural problems.

Huginn is biased toward:
- environmental contact,
- tool use,
- evidence gathering,
- forward-looking interpretation.

## 3.3 Muninn

Muninn is **memory / meaningful return**.

Primary role:
- compare new evidence to memory and transcripts,
- detect novelty vs repetition,
- summarize what matters,
- compress signal into spine-ingestible form,
- classify return disposition,
- identify whether a finding should be ephemeral, daily, durable, or escalated.

Muninn is biased toward:
- memory alignment,
- continuity,
- compaction,
- return quality.

## 3.4 Aviary

The aviary is an isolated interaction zone where ravens may exchange findings outside the spine.

Purpose:
- let Huginn and Muninn compare or challenge interpretations,
- preserve visible intermediate reasoning,
- avoid forcing every micro-exchange through the spine.

Constraints:
- aviary interaction is logged,
- aviary interaction does not directly mutate canonical memory,
- only the spine can accept a raven return into durable state.

## 3.5 Grafts

A graft is a proposed **additive structural change** to Ygg.

Examples:
- add a new protocol,
- add a new adapter,
- add a new policy file,
- add a new branch/workstream,
- add a new observable runtime surface,
- add a new recurring check or agent loop.

A graft is lawful growth only if it has:
- an attachment point,
- rationale,
- expected benefit,
- failure conditions,
- a governance path.

## 3.6 Beaks

A beak is a proposed **subtractive or reshaping action**.

Examples:
- mark stale branches,
- archive obsolete structures,
- deprecate a protocol,
- trim duplicated bark/docs,
- disable a failing loop,
- delete or rewrite structure.

Beaks come in two classes:

### Soft beaks
- mark,
- warn,
- archive,
- recommend,
- quarantine,
- deprecate.

### Hard beaks
- delete,
- disable,
- rewrite,
- prune aggressively,
- alter structure irreversibly.

v1 rule:
- soft beaks may be proposed freely,
- hard beaks are HITL-gated by default.

---

## 4. Invariants

1. RAVENS is not canonical memory.
2. Meaningful external flights must end in explicit disposition.
3. RavENS may gather signal, but the spine decides what becomes durable.
4. Tool use must be visible through artifacts or logs.
5. Grafts and beaks must name their target structure.
6. No destructive structural action occurs silently.
7. Muninn must preserve evidence linkage; return without evidence is weak by default.
8. Raven symbolism must map to inspectable behavior, not decorative language.

---

## 5. Observability requirements

The human operator should be able to observe all five of these surfaces.

## 5.1 Ravens interacting with environment

Each flight should make it possible to inspect:
- what triggered launch,
- what tools/surfaces were touched,
- what evidence was gathered,
- what was ignored.

## 5.2 Ravens interacting with each other outside spine

Aviary interaction should expose:
- which ravens interacted,
- what claims they exchanged,
- where they agreed/disagreed,
- what return package emerged.

## 5.3 Spine routing and acceptance behavior

Spine adjudication should show:
- what came back,
- what was accepted, rejected, parked, or escalated,
- what evidence influenced the decision,
- what consequences followed.

## 5.4 Grafting activity

The system should expose:
- proposed new attachments,
- target branch or structural site,
- why growth is needed,
- status of the graft.

## 5.5 Beak activity

The system should expose:
- target of pruning or reshaping,
- whether the beak is soft or hard,
- evidence for decay/duplication/drift,
- approval status,
- resulting action.

---

## 6. v1 lifecycle

A raven flight in v1 follows this lifecycle.

1. **Commissioned**
   - the spine creates a flight request.

2. **Launched**
   - one or both ravens receive scope, purpose, and permissions.

3. **Gathering**
   - Huginn and/or Muninn interacts with tools, memory, transcripts, env, or files.

4. **Aviary exchange** (optional)
   - ravens compare findings or challenge each other.

5. **Return packaged**
   - Muninn produces a structured return packet.

6. **Adjudicated by spine**
   - the spine accepts, rejects, parks, trials, or escalates.

7. **Effected**
   - if accepted, a graft/beak/task/write is created through governed paths.

8. **Closed**
   - the flight records final disposition and consequences.

No flight should terminate in ambiguous limbo if it produced meaningful evidence.

---

## 7. Trigger types

A flight may be commissioned from any of these trigger classes.

1. **Human request**
2. **Scheduled check**
3. **Heartbeat prompt**
4. **Environment signal**
5. **Project-state anomaly**
6. **Memory inconsistency**
7. **Proposal seed**
8. **Spine curiosity / exploratory scan**

---

## 8. Permission model

## 8.1 Default Huginn permissions

Default bias: read-mostly.

Allowed by default:
- file reads,
- transcript reads,
- memory search/get,
- web fetch/search,
- status/inspection commands,
- non-destructive env inspection,
- proposal drafting.

Not allowed by default:
- destructive file edits,
- irreversible external actions,
- secret exfiltration,
- policy rewrites without adjudication.

## 8.2 Default Muninn permissions

Allowed by default:
- memory comparison,
- transcript comparison,
- compaction/summarization,
- return packet drafting,
- promotion recommendation.

Not allowed by default:
- silent durable writes,
- hidden state mutation,
- bypassing spine promotion rules.

## 8.3 Aviary permissions

Allowed:
- structured exchange of evidence, claims, doubts, and recommendations.

Not allowed:
- canonical memory writes,
- durable promotion,
- hard-beak execution.

## 8.4 Beak permissions

Soft beaks:
- may draft warnings, deprecations, archive suggestions, and cleanup proposals.

Hard beaks:
- require HITL by default.

---

## 9. Return classes and spine adjudication

Raven returns should map onto existing Ygg disposition doctrine.

## 9.1 Spine adjudication states

The spine must assign one of:
- `REJECT`
- `PARK`
- `TRIAL`
- `ADOPT`
- `ESCALATE_HITL`

## 9.2 Promotion/disposition mapping

The return should also map to one of:
- `NO_PROMOTE`
- `LOG_DAILY`
- `PROMOTE_DURABLE`
- `ESCALATE_HITL`

Suggested mapping:
- `REJECT` -> `NO_PROMOTE`
- `PARK` -> `LOG_DAILY`
- `TRIAL` -> `LOG_DAILY` or bounded experimental write
- `ADOPT` -> `PROMOTE_DURABLE`
- `ESCALATE_HITL` -> `ESCALATE_HITL`

---

## 10. Artifact model

v1 should produce real files for inspectability.

Suggested layout:

```text
~/ygg/state/runtime/ravens/
  flights/
    RAVEN-*.json
  logs/
    RAVEN-*.jsonl
  aviary/
    AVIARY-*.jsonl
  returns/
    RAVEN-*.md
  grafts/
    GRAFT-*.md
  beaks/
    BEAK-*.md
```

Human-readable mirrors are welcome as long as machine-readable artifacts remain canonical.

---

## 11. Event schema

Minimum event object:

```json
{
  "id": "RAVEN-2026-03-15-001",
  "flightId": "RAVEN-2026-03-15-001",
  "phase": "gathering",
  "actor": "huginn",
  "timestamp": "2026-03-15T16:00:00-04:00",
  "trigger": "human-request",
  "purpose": "Inspect current filesystem/package boundary and propose RAVENS spec",
  "surface": "filesystem",
  "action": "read",
  "target": "~/ygg/docs",
  "evidenceRefs": [
    "file:~/ygg/docs/RAVENS.md"
  ],
  "notes": "Observed existing conceptual raven draft; implementation contract still missing."
}
```

Minimum return packet frontmatter:

```yaml
id: RAVEN-2026-03-15-001
status: returned
actors:
  - huginn
  - muninn
trigger: human-request
claim_tier: defensible-now
adjudication: PARK
promotion: LOG_DAILY
contains_graft: true
contains_beak: false
```

Return sections:
- Objective
- Evidence
- Interpretation
- Dissent / uncertainty
- Recommended action
- Failure conditions
- Graft / Beak proposals
- Promotion recommendation

---

## 12. Graft contract

A graft proposal must include:
- `id`
- `title`
- `target_attachment`
- `why_now`
- `inputs`
- `expected_benefit`
- `failure_conditions`
- `risk_class`
- `adoption_path`

Example attachment points:
- `docs/`
- `lib/ygg/`
- `machine/`
- `state/policy/`
- `state/scripts/`
- `memory/daily/`
- `memory/long-term/`

A graft that cannot name its attachment point is underspecified.

---

## 13. Beak contract

A beak proposal must include:
- `id`
- `class` (`soft` or `hard`)
- `target`
- `problem_type` (`rot`, `duplication`, `drift`, `deadwood`, `misgrowth`)
- `evidence`
- `suggested_action`
- `reversibility`
- `approval_required`
- `failure_if_not_done`

Defaults:
- archive/move is preferred over delete,
- reversible actions are preferred over irreversible actions,
- hard beaks require HITL unless explicitly policy-approved.

---

## 14. Reality-coupling rules

RAVENS fails if it becomes myth without operational consequence.

Therefore every meaningful flight must produce at least one of:
- tool evidence,
- file evidence,
- transcript evidence,
- memory comparison,
- actionable proposal,
- explicit no-op disposition.

Weak return examples:
- purely aesthetic speculation,
- metaphor with no target structure,
- proposal without evidence,
- pruning recommendation without identified decay.

Strong return examples:
- cites env state,
- compares against memory,
- names a concrete target,
- states uncertainty,
- proposes lawful next action.

---

## 15. Failure conditions

RAVENS v1 is failing if:
- ravens become decorative language for ordinary tool calls,
- flights happen with no inspectable traces,
- aviary interactions become hidden chatter,
- spine accepts returns without evidence,
- grafts are proposed without attachment points,
- hard beaks execute without approval,
- raven outputs bypass canonical promotion rules,
- the system produces more symbolic complexity than operational clarity.

---

## 16. Minimal implementation slice (what Codex should build first)

Build the smallest useful slice.

### Slice A — inspectable read-only raven flights
- Commission a flight.
- Log flight events to `state/runtime/ravens/logs/`.
- Let Huginn inspect a limited set of surfaces.
- Let Muninn package a return.
- Let the spine record adjudication.

### Slice B — proposal-capable returns
- Support graft proposals as files.
- Support soft-beak proposals as files.
- No automatic destructive action yet.

### Slice C — aviary exchange
- Allow Huginn/Muninn exchange in a logged, isolated format.
- Keep spine as the final adjudicator.

Do **not** implement autonomous hard-beak execution in v1.

---

## 17. Suggested initial command surface

These verbs are suggested, not mandatory.

```text
ygg raven launch
ygg raven status
ygg raven inspect <flight-id>
ygg raven trace <flight-id>
ygg raven probe <flight-id> <surface>
ygg raven aviary <flight-id> <topic>
ygg raven return <flight-id>
ygg graft propose
ygg beak propose
```

A single `ygg raven` namespace is preferred to avoid exploding top-level verbs too early.

---

## 18. Acceptance tests

RAVENS v1 should not be considered implemented until all of these pass.

1. A flight can be commissioned with explicit trigger + purpose.
2. Huginn can inspect at least one real surface and log it.
3. Muninn can compare gathered evidence to memory/transcript context.
4. A return packet is produced with evidence refs and failure conditions.
5. Spine adjudication is recorded explicitly.
6. A graft proposal can be emitted as an artifact.
7. A soft-beak proposal can be emitted as an artifact.
8. Aviary interaction, if present, is logged and inspectable.
9. No durable write happens without a spine decision.
10. No hard-beak action occurs without HITL approval.

---

## 19. Short version

RAVENS v1 makes roaming cognition real.

- Huginn goes outward.
- Muninn makes return meaningful.
- The aviary lets ravens compare without bypassing governance.
- The spine commissions, judges, and promotes.
- Grafts grow the tree.
- Beaks prune or reshape it.
- Everything meaningful remains observable, evidence-linked, and reality-coupled.

If the ravens cannot return with consequence, they are not yet worthy ravens.
