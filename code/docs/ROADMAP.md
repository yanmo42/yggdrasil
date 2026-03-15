# Roadmap

## Phase 0 — Scaffold

Status: complete.

- [x] Create `~/ygg`
- [x] Create docs for vocabulary and architecture
- [x] Add links back to current implementation
- [x] Add thin CLI wrapper

## Phase 1 — Vocabulary lock

Goal: settle naming before deeper code moves.

- [x] confirm CLI namespace (`ygg`)
- [x] confirm command family verbs
- [x] define which nouns are canonical
- [x] write a verb/spec document for the command family

## Phase 2 — Thin wrapper parity

Goal: make `~/ygg/bin/ygg` a reliable entrypoint over current code.

- [x] `ygg work`
- [x] `ygg root`
- [x] `ygg branch`
- [x] `ygg resume`
- [x] `ygg status`
- [x] stable help text
- [x] `ygg forge`

## Phase 3 — Promotion-aware flows

Goal: make branch outcomes explicit.

- [x] define disposition schema
- [x] wire `promote` command
- [x] add Ygg-local evidence/result record structure
- [ ] make daily/durable writes more intentional

## Phase 4 — Source migration

Goal: move selected implementation into `~/ygg/src/` without losing clarity.

- [ ] decide what should remain in assistant-home
- [ ] decide what should become Ygg-native code
- [ ] move or re-export modules cleanly
- [ ] update docs and links

## Phase 5 — Interface and co-reasoning layer

Goal: reduce command-structure burden on the human without losing inspectability.

- [x] add natural-language guidance layer that can translate fuzzy intent into suggested Ygg commands (`ygg suggest`)
- [ ] add response cards / suggested next commands after major actions
- [x] add `ygg explain <verb>` affordances
- [x] add `ygg help <verb>` affordances
- [ ] add a per-command plain-English Q&A section for specialized contexts ("how would this command work for X?")
- [ ] explore lightweight TUI/GUI as an optional interface, not a requirement
- [ ] prototype branch topology visualization in 2D as an inspectable interface layer
- [ ] explore AR/VR branch visualization once 2D semantics are stable
- [ ] preserve deterministic underlying commands even when the surface becomes more conversational
- [ ] design the interface as a human/machine hybrid workflow rather than a one-sided automation shell

## Guardrails

- preserve current working behavior while refactoring
- avoid premature mythic naming overload
- keep human inspectability as a first-class requirement
- do not move authoritative code until the structure is clearly better
