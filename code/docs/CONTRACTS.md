# Command Contracts (Ygg v1)

This file makes verb behavior explicit so human/machine usage stays aligned.

## Contract conventions

### ID normalization
- `domain` and `task` inputs are normalized to slug form (`lowercase-with-dashes`).
- Example: `Website Dev` → `website-dev`.

### Mutability classes
- `false`: no state writes.
- `true`: direct writes to baton/log state.
- `indirect`: sends control packets / invokes wrappers that may update state downstream.

### Exit semantics
- `0` success.
- non-zero means the underlying command or argument resolution failed.
- `argparse` usage errors return non-zero (typically `2`).

---

## `ygg suggest`

- mutates state: `false`
- requires: `request`
- optional: `--domain`, `--task`, `--json`
- writes: none
- guarantees:
  - never executes suggested commands
  - prints route interpretation (`action`, `confidence`, `reason`, target when available)
  - returns at least one concrete `ygg` command suggestion
- fails when:
  - request is empty
  - workspace planner/router imports are unavailable

## `ygg work`

- mutates state: `indirect`
- requires: none
- optional: `request...`
- writes: delegated to workspace work wrapper / planner session
- guarantees:
  - forwards arguments verbatim to workspace `scripts/work.py`
- fails when:
  - workspace `work.py` is missing or exits non-zero

## `ygg root`

- mutates state: `indirect`
- requires: none
- optional: `request...`, `--session`, `--openclaw-bin`, `--print-packet`
- writes: planner message stream (unless `--print-packet`)
- guarantees:
  - forced route action = `stay_in_planner`
  - does not auto-pick branch/forge actions
- fails when:
  - planner imports are unavailable
  - OpenClaw launch fails when not in print mode

## `ygg branch`

- mutates state: `true`
- requires: `domain`, `task`
- optional:
  - `--objective`, `--current-state`, `--next-action`
  - `--status`, `--priority`
  - `--locked`, `--rejected`, `--reopen`, `--artifact` (repeatable)
  - `--agent`, `--dry-run`
- writes: workspace resume baton files via `resume checkpoint`
- guarantees:
  - creates/updates explicit lane state
  - prints resulting domain status on success
- fails when:
  - checkpoint command exits non-zero

## `ygg resume`

- mutates state: `indirect`
- requires: none
- optional: `domain`, `task`, `--semantic`, `--max-chars`, `--agent`, `--openclaw-bin`, `--print-only`
- writes: planner message stream when launching
- guarantees:
  - resolves explicit target, or auto-targets sole active task
  - supports packet-only inspection mode
- fails when:
  - multiple active tasks exist and no explicit target is provided
  - target resolution is ambiguous
  - resume command exits non-zero

## `ygg forge`

- mutates state: `indirect`
- requires: none
- optional: `request...`, `--domain`, `--task`, `--session`, `--openclaw-bin`, `--print-packet`
- writes: planner message stream (unless `--print-packet`)
- guarantees:
  - forced route action = `suggest_spawn_codex`
  - requires unambiguous lane target
- fails when:
  - no active task exists and no explicit target is provided
  - target resolution is ambiguous
  - OpenClaw launch fails when not in print mode

## `ygg promote`

- mutates state: `true`
- requires: `domain`, `task`, `--disposition`
- optional: `--note`, `--artifact` (repeatable), `--finish`, `--dry-run`
- writes:
  - `~/ygg/state/promotions.jsonl`
  - `~/ygg/notes/promotions.md`
  - optional workspace baton updates (`checkpoint`/`finish`)
- guarantees:
  - records explicit disposition with timestamp
  - supports no-write dry-run mode
- fails when:
  - disposition is invalid/missing
  - follow-up checkpoint/finish command exits non-zero

## `ygg status`

- mutates state: `false`
- requires: none
- optional: `domain`
- writes: none
- guarantees:
  - prints current baton summary for all domains or one domain
- fails when:
  - resume status command exits non-zero

---

## Discoverability

- `ygg explain <verb>` and `ygg help <verb>` expose these contracts inline.
- `ygg explain --json` / `ygg help --json` return machine-readable contract fields.
