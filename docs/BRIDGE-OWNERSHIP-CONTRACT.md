# Bridge Ownership Contract

Status: active contract
Scope: ownership boundaries across Ygg, assistant-home/OpenClaw runtime state, Sandy Chaos canon, and bridge surfaces
Audience: Ian + Ygg

## Purpose

This contract makes one thing explicit:

Ygg is only reliable as a control plane if it stays honest about what it owns, what it derives, what it merely bridges to, and what remains canonical somewhere else.

## Ownership classes

### `ygg-canonical`
Authoritative Ygg repo content.

Examples:
- `lib/ygg/*.py`
- `state/ygg/checkpoints/`
- `state/ygg/programs.json`
- `state/ygg/ideas.json`
- canonical repo docs under `docs/`

Rules:
- may be mutated by Ygg repo commands that explicitly declare writes
- should be commit-safe unless a state policy says otherwise
- should be treated as authoritative for Ygg behavior and semantics

### `ygg-derived`
Reproducible or inspectable outputs derived from canonical state.

Examples:
- retrieval indexes/benchmarks generated from canonical continuity surfaces
- inventory summaries
- future topology views derived from checkpoints/programs/ideas

Rules:
- may be regenerated
- should not silently replace canonical state
- should say what canonical inputs they were derived from

### `assistant-local`
Assistant-home / OpenClaw local runtime, memory, embodiment, or machine-specific state.

Examples:
- `~/.openclaw/workspace-claw-main/core/MEMORY.md`
- `~/.openclaw/workspace-claw-main/memory/daily/*`
- OpenClaw runtime DBs and local memory stores
- machine/session embodiment snapshots for one live environment

Rules:
- not canonical Ygg repo truth
- may be consumed via explicit bridges or adapters
- should not be committed into Ygg as if portable or global

### `sc-canonical`
Authoritative Sandy Chaos research truth surfaces.

Examples:
- canonical SC theory docs
- benchmark definitions owned by Sandy Chaos
- theory or evidence artifacts whose truth conditions belong to the SC repo

Rules:
- Ygg may read, audit, summarize, route, or reference
- Ygg does not become the authority for these artifacts merely by indexing them
- bridge docs must not blur Ygg operational state with SC canonical claims

### `bridge`
Explicit adapters or interfaces that connect ownership domains without erasing the boundary.

Examples:
- inventory surfaces describing Ygg vs assistant-home vs SC ownership
- event couriers that emit into local notes or promotion sinks
- path contracts and integration docs
- future audit/report surfaces spanning multiple repos

Rules:
- bridge code must name the upstream canonical source honestly
- bridge outputs should preserve provenance
- bridge commands must not imply cross-domain mutation authority they do not actually have

## Mutation authority

### Ygg commands may mutate
- `ygg-canonical` state when the command contract explicitly says so
- selected `ygg-derived` outputs when the generation path is explicit and inspectable

### Ygg commands should not silently mutate
- `assistant-local` memory/state as if it were Ygg canon
- `sc-canonical` research truth surfaces without explicit repo/context intent
- cross-domain surfaces through undocumented side effects

## Canonical vs derived vs runtime

### Canonical
The source of truth for a Ygg semantic concept or command contract.

### Derived
A reproducible readout computed from canonical sources.

### Runtime
Live environment outputs, embodiment snapshots, couriers, logs, caches, or machine-local notes.

A runtime surface can matter operationally without becoming canonical.

## Path-level guidance

### Ygg semantic continuity
- canonical: `state/ygg/checkpoints/`, `state/ygg/programs.json`, `state/ygg/ideas.json`
- derived: retrieval/benchmark summaries or topology views computed from those files

### Ygg runtime continuity
- canonical code: `lib/ygg/heimdall.py`, `lib/ygg/ratatoskr.py`
- runtime outputs: files under `state/runtime/` and explicit note sinks
- bridge caution: runtime outputs may describe a machine truth, not a repo truth

### Assistant-home continuity
- local memory and daily notes remain assistant-local
- Ygg may define schemas/adapters for them without claiming their literal content as canonical

### Sandy Chaos integration
- Ygg may track frontiers, audits, and next-step pressure
- Sandy Chaos remains canonical for research claims and theory artifacts

## Operational rule of thumb

If a surface answers “what is true for Ygg itself?”, it is probably `ygg-canonical`.

If it answers “what did the current machine/session/runtime observe?”, it is probably `assistant-local` or runtime.

If it answers “what is true for Sandy Chaos research?”, it is probably `sc-canonical`.

If it exists mainly to connect those answers without erasing provenance, it is a `bridge`.
