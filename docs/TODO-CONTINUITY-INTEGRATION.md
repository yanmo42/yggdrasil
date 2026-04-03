# TODO — Continuity Integration

This file tracks the remaining work after the 2026-04-02 continuity/schema planning pass.

## Done in this checkpoint
- audited the OpenClaw ↔ Ygg continuity boundary
- documented canonical ownership split
- documented continuity schema / state model
- added starter semantic registry files:
  - `state/ygg/programs.json`
  - `state/ygg/ideas.json`
- added runtime self template:
  - `state/templates/ygg-self.example.json`

## Remaining implementation work

### 1. Promote Heimdall into `~/ygg`
- [x] ported into `lib/ygg/heimdall.py`
- [x] removed assistant-home-only imports
- [x] default runtime snapshot path now targets Ygg-local runtime state (`state/runtime/ygg-self.json`)

### 2. Promote Ratatoskr into `~/ygg`
- [x] ported into `lib/ygg/ratatoskr.py`
- [x] supports Ygg-owned note/promotion sinks
- [x] keeps assistant-home-style daily memory as an adapter pattern rather than canonical ownership

### 3. Decide final module/CLI shape
- [x] added Ygg-native CLI access (`ygg heimdall`, `ygg ratatoskr`)
- [ ] document how runtime continuity commands relate to existing `checkpoint` / `promote` / `status --continuity`

### 4. Clarify semantic registry update flows
- decide how `programs.json` and `ideas.json` are updated:
  - explicit operator edits
  - explicit commands
  - bounded checkpoint/promote flows
- avoid hidden automatic mutation of semantic state

### 5. Optional later
- add `state/ygg/topology.json` only if ideas/programs/checkpoints make the need obvious
- add list/edit/status command affordances for programs/ideas when useful

### 6. Pre-commit bootstrap hardening
- [x] make bootstrap/path-contract generation honor CLI and env root overrides end-to-end
  - current issue: `machine/bootstrap-host.sh` can write `ygg-paths.yaml` with default roots even when `--workspace-root` / `--projects-root` were explicitly passed
  - likely fix: pass the resolved shell overrides through to `machine/render-path-contract.py` or teach the renderer to accept explicit override env/flags
- [x] make post-bootstrap path validation check the contract that bootstrap just wrote
  - current issue: `run_path_checks()` can validate the ambient/default contract instead of `PATH_CONTRACT_FILE`
  - likely fix: call `ygg paths check --paths-file "$PATH_CONTRACT_FILE"` or equivalent python fallback
- [x] replace partial-upgrade-style Arch install behavior
  - current issue: package install currently uses `pacman -Sy --needed ...`, which is not the safe Arch recovery pattern
  - likely fix: switch to a full upgrade/install flow or an explicitly supported Arch bootstrap strategy
- [x] make `ygg bootstrap inspect` reflect real bootstrap override resolution
  - current issue: inspect currently shows profile-file defaults but ignores live env overrides and can preview the wrong contract path
  - likely fix: merge profile env with process env / explicit args before resolving assignments and path-contract preview
- [x] add tests for root override behavior
  - cover bootstrap contract generation with custom `WORKSPACE_ROOT` / `PROJECTS_ROOT`
  - cover `ygg bootstrap inspect` with env or flag overrides so drift is caught automatically

## Guiding rule
Do not collapse:
- semantic continuity state,
- runtime embodiment state,
- and assistant-home personal memory

into one blob. Keep ownership explicit.
