# Port Manifest — workspace-claw-main → yggdrasil

Date: 2026-04-03
Target branch: `port/workspace-sync-2026-04-03`
Source repo: `/home/ian/.openclaw/workspace-claw-main` (`yanmo42/potential-telegram`)
Target repo: `/home/ian/ygg` (`yanmo42/yggdrasil`)

## Goal
Port the work completed this session into `yggdrasil/main` in clean, reviewable batches.

## Source commits reviewed
- `190b6f5` feat(ygg): wire canonical continuity kernel loop
- `ff03823` feat(resume): add dashboard wake flow and adaptive nvrsleep launch defaults
- `ff69450` test(ratatoskr): add runtime routing tests and package exports
- `4c46989` docs(core): codify YGG continuity startup and embodiment notes
- `05f07e3` chore(state): checkpoint persona and resume runtime pointers
- `71bc3e7` docs(memory): add March-April session notes and daily logs
- `c49f118` feat(research): add worldline-gear simulation docs and helper scripts

## Batch plan (ordered)

### Batch 1 — Continuity core parity (highest priority)
**Intent:** ensure Heimdall/Ratatoskr/YGG continuity goals are concretely present in yggdrasil.

Source surfaces:
- `tools/heimdall_v1/runtime.py`
- `tools/ratatoskr_v1/runtime.py`
- `scripts/heimdall.py`
- `scripts/ratatoskr.py`
- `state/ygg-self.json`
- `state/ygg-kernel.json`
- `core/YGG.md`
- `core/YGG-OPERATING-BASELINE.md`
- `core/RATATOSKR.md`

Target mapping in yggdrasil:
- `lib/ygg/heimdall.py` (merge parity deltas)
- `lib/ygg/ratatoskr.py` (merge parity deltas)
- `bin/ygg` + command entrypoints (if wrapper behavior needs exposure)
- `docs/CONTINUITY-OPS-V1.md` + related docs (contract docs merged here)
- `state/runtime/*` and `state/notes/*` conventions (align with ygg layout)

Result commit title (planned):
- `feat(continuity): align heimdall/ratatoskr runtime loop with workspace implementation`

### Batch 2 — Resume launch improvements
**Intent:** port practical resume launch/wake upgrades (dashboard wake + adaptive thinking defaults).

Source surfaces:
- `tools/resume_v1/cli.py`
- `tools/resume_v1/daily.py`
- `tools/resume_v1/README.md`
- `pods/resume-baton-v1/SPEC.md`
- `tests/test_cli.py`

Target mapping in yggdrasil:
- ygg CLI lane/resume command implementation (under `lib/ygg/*` + `commands/*`)
- docs under `docs/` (resume/wake procedure details)
- tests under `tests/` mapped to ygg CLI modules

Result commit title (planned):
- `feat(resume): add dashboard wake procedure and adaptive nvrsleep launch policy`

### Batch 3 — Tests/package glue
**Intent:** keep test coverage in sync for continuity surfaces.

Source surfaces:
- `tests/test_ratatoskr.py` (workspace variant)
- `tests/test_heimdall.py` (workspace variant)
- package `__init__` exports under `tools/*`

Target mapping in yggdrasil:
- update existing `tests/test_ratatoskr.py` and `tests/test_heimdall.py`
- expose any missing public symbols in `lib/ygg/*` as needed

Result commit title (planned):
- `test(continuity): extend heimdall/ratatoskr coverage for runtime event routing`

### Batch 4 — Optional carryover (not core to ygg runtime)
**Intent:** decide explicitly whether to import workspace-only memory/research artifacts.

Source surfaces:
- `memory/*.md`, `memory/daily/*.md`
- worldline/gears docs + simulators

Decision needed:
- Keep as assistant-home history only, OR
- import selected artifacts into ygg docs archive (`docs/notes/` or `docs/archive/`)

No automatic port until explicitly approved.

### Not ported as code
- runtime pointer files (`state/persona-mode.json`, `state/resume/*`) are environment-local and should not be blindly synced unless intentionally versioned for ygg runtime.

## Success criteria
1. yggdrasil contains the intended continuity behavior (not just file copies).
2. tests pass in `/home/ian/ygg`.
3. changes are split into small coherent commits.
4. branch merged/pushed to `main` with clear history.

## Execution notes
- Branch created: ✅ `port/workspace-sync-2026-04-03`
- Next immediate action: implement Batch 1 and commit.
