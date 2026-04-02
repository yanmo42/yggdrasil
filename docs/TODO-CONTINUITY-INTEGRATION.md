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
- port `scripts/heimdall.py` / `tools/heimdall_v1/runtime.py` into Ygg-native module(s)
- remove assistant-home-only imports
- default runtime snapshot path should be Ygg-local runtime state, not committed semantic state

### 2. Promote Ratatoskr into `~/ygg`
- port `scripts/ratatoskr.py` / `tools/ratatoskr_v1/runtime.py` into Ygg-native module(s)
- support pluggable sinks/adapters
- keep assistant-home daily memory as an optional adapter, not canonical ownership

### 3. Decide final module/CLI shape
- likely add Ygg-native CLI access for Heimdall/Ratatoskr
- document how runtime continuity commands relate to existing `checkpoint` / `promote` / `status --continuity`

### 4. Clarify semantic registry update flows
- decide how `programs.json` and `ideas.json` are updated:
  - explicit operator edits
  - explicit commands
  - bounded checkpoint/promote flows
- avoid hidden automatic mutation of semantic state

### 5. Optional later
- add `state/ygg/topology.json` only if ideas/programs/checkpoints make the need obvious
- add list/edit/status command affordances for programs/ideas when useful

## Guiding rule
Do not collapse:
- semantic continuity state,
- runtime embodiment state,
- and assistant-home personal memory

into one blob. Keep ownership explicit.
