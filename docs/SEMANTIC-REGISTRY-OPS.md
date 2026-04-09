# Semantic Registry Operations

This document defines the intended command surface for mutating Ygg semantic registry state.

Authoritative files:
- `state/ygg/programs.json`
- `state/ygg/ideas.json`

These are semantic registry state, not chat memory and not runtime-only event logs.

## Design rules

- mutations must be explicit
- ids are stable
- registry JSON remains authoritative
- commands should prefer patch semantics over opaque regeneration
- links should be stored in the existing schema style rather than inventing a second topology authority

## Proposed command surface

### Programs
- `ygg program list`
- `ygg program show <id>`
- `ygg program add ...`
- `ygg program update <id> ...`

### Ideas
- `ygg idea list`
- `ygg idea show <id>`
- `ygg idea add ...`
- `ygg idea update <id> ...`
- `ygg idea link <id> --program ... --checkpoint ... --promotion-target ...`

## Intended behavior

### `ygg program add`
Create a new program record with explicit fields such as:
- `id`
- `title`
- `status`
- `kind`
- `summary`
- `owner`
- `priority`
- `relatedLanes`
- `artifacts`
- `nextAction`

Example:
`ygg program add --id semantic-registry-ops --title "Semantic registry operations" --status active --kind productization --related-lane continuity --artifact docs/SEMANTIC-REGISTRY-OPS.md`

### `ygg program update <id>`
Patch one existing program record.
Do not rewrite unrelated records.

Example:
`ygg program update semantic-registry-ops --status blocked --next-action "Resolve validation edge cases"`

### `ygg idea add`
Create a new idea record with explicit fields such as:
- `id`
- `title`
- `status`
- `summary`
- `claimTier`
- `origin`
- `nextAction`
- `tags`

Example:
`ygg idea add --id registry-link-flow --title "Registry link flow" --status incubating --claim-tier plausible --tag continuity`

### `ygg idea update <id>`
Patch one existing idea record.
Do not erase existing links unless the operator explicitly changes them.

Example:
`ygg idea update registry-link-flow --status testing --summary "CLI mutation flow is implemented"`

### `ygg idea link <id>`
Append semantic links to an idea in the existing schema shape:
- `links.programs[]`
- `links.checkpoints[]`
- `links.promotionTargets[]`

This command should dedupe entries rather than creating repeated links.

Example:
`ygg idea link registry-link-flow --program semantic-registry-ops --checkpoint state/ygg/checkpoints/example.json --promotion-target docs/SEMANTIC-REGISTRY-OPS.md`

## Validation expectations

### Program statuses
- `active`
- `watching`
- `blocked`
- `hibernating`
- `completed`
- `dropped`

### Idea statuses
- `incubating`
- `testing`
- `parked`
- `adopted`
- `rejected`

### Claim tiers
- `defensible`
- `plausible`
- `speculative`

## Non-goals for this phase

- hidden checkpoint creation on every mutation
- a canonical `topology.json`
- GUI/TUI management surfaces
- automatic promotion logic

## Why this matters

Ygg can now retrieve over semantic state.
The next step is to let Ygg maintain that semantic state cleanly, explicitly, and inspectably.
