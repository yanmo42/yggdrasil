# Ygg Architecture Sketch

## Purpose

Provide a human-legible command surface for branching work without losing a coherent center.

## Core model

### Spine
The spine is the planner/control plane.
It owns:

- routing
- governance
- approval handling
- continuity rules
- promotion decisions

### Branches
Branches are bounded local work processes.
Examples:

- a repo task
- an implementation lane
- a research pass
- a verification pass
- a temporary exploration

Branches are not errors. They are how variation happens.

### Promotion
Meaningful branch outcomes should not disappear silently.
A branch should end in an explicit disposition such as:

- `NO_PROMOTE`
- `LOG_DAILY`
- `PROMOTE_DURABLE`
- `ESCALATE_HITL`

## Temporal cadence

### Fast loop
Per-invocation routing and local execution.

### Meso loop
Daily summaries, baton checkpoints, digesting, routing cleanup.

### Slow loop
Durable policy, architecture, and contract updates.

## Bounded branch contract

A healthy branch should carry a compact contract:

- goal
- constraints
- definition of done
- validation command
- expected disposition
- evidence artifact(s)
- decision gate

## Current implementation relationship

Right now the implementation is split:

- command front door in assistant-home workspace
- baton state in `state/resume/`
- planner packet assembly in `tools/work_v1/`
- this `~/ygg` directory as the human-facing organizational home

That is acceptable in the short term.

## Near-term design principle

The command family should improve **branch lifecycle governance**, not merely task launching.

That means:

- better routing
- clearer boundaries
- explicit promotion
- inspectable evidence
- lower context drift

## Failure condition

The architecture is failing if it becomes:

- more bureaucratic than helpful
- harder to use than the context loss it prevents
- poetic in wording but muddy in operation
