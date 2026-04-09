# Topology-Aware Continuity Retrieval

Status: planned
Owner: ian + ygg
Created: 2026-04-08
Idea id: `topology-aware-continuity-retrieval`
Program: `ygg-continuity-integration`

## Goal

Implement a benchmarkable retrieval layer for Ygg that treats continuity state as a connected topology rather than a flat bag of text.

The first release should retrieve over existing Ygg-owned surfaces:
- `state/ygg/checkpoints/`
- `state/ygg/ideas.json`
- `state/ygg/programs.json`
- `state/runtime/event-queue.jsonl`
- `state/runtime/promotions.jsonl`

It should compare:
- keyword baseline
- recency baseline
- topology-aware hybrid retrieval

## Constraints

- Do not introduce a canonical `state/ygg/topology.json` unless the derived approach proves insufficient.
- Keep authoritative state in the existing files.
- Make retrieval explainable and inspectable.
- Start with Ygg-local continuity surfaces only.
- Add tests and a benchmark harness before calling the feature complete.

## Deliverables

1. A normalized continuity corpus adapter.
2. A derived graph/topology builder over existing continuity artifacts.
3. A benchmark dataset with ~30 evaluation queries.
4. Retrieval baselines:
   - keyword
   - recency
   - topology-aware hybrid
5. CLI commands to query and benchmark retrieval.
6. Tests covering normalization, graph derivation, scoring, and CLI behavior.

## Phase 1 — Corpus normalization

Create a retrieval module that loads and normalizes existing continuity artifacts into a shared internal record shape.

Proposed fields:
- `id`
- `kind`
- `title`
- `summary`
- `text`
- `timestamp`
- `authority`
- `tags`
- `links`
- `sourcePath`
- `metadata`

Acceptance:
- Can load all target Ygg surfaces without mutating them.
- Produces stable record ids and source references.
- Has tests for each source type.

## Phase 2 — Derived topology

Build a derived graph from the normalized corpus.

Initial edge types:
- idea -> checkpoint
- idea -> program
- program -> related lane
- event -> lane/task/session when link metadata exists
- promotion -> domain/task/artifact associations
- shared tags / shared lane / shared artifact as soft links

Acceptance:
- Graph is derived, inspectable, and reproducible from authoritative state.
- No new canonical topology store is required.
- Tests cover explicit and inferred links.

## Phase 3 — Benchmark harness

Add a benchmark file with approximately 30 queries.

Each benchmark case should include:
- `query`
- `expectedIds`
- `acceptableIds`
- `why`
- `category`

Suggested categories:
- next-action retrieval
- ownership/program linkage
- runtime continuity lookup
- active vs incubating distinction
- artifact/source lookup
- cross-surface continuity retrieval

Acceptance:
- Benchmark can run from CLI and test suite.
- Baselines are compared on the same cases.

## Phase 4 — Baselines

Implement at least:

### 4.1 Keyword baseline
Simple lexical/token overlap retrieval over normalized text.

### 4.2 Recency baseline
Return the most recent relevant continuity items using timestamp-heavy ranking.

### 4.3 Topology-aware hybrid
Combine:
- lexical match
- authority weighting
- recency decay
- explicit-link bonus
- graph-neighborhood bonus
- same-program / same-lane / same-tag bonus

Acceptance:
- Results are explainable.
- Hybrid outperforms naive recency on meaningful benchmark slices.
- Scoring weights are easy to inspect and adjust.

## Phase 5 — CLI

Add user-facing commands, likely:
- `ygg retrieve <query>`
- `ygg retrieve <query> --json`
- `ygg retrieve <query> --strategy keyword|recency|topology`
- `ygg retrieve <query> --explain`
- `ygg retrieve-benchmark`

Acceptance:
- Human-readable and JSON modes both exist.
- `--explain` shows why top results scored well.
- Benchmark output makes baseline comparison obvious.

## Phase 6 — Validation and polish

- Add integration tests.
- Validate on the current repo’s live state.
- Document the feature in `docs/` and `README.md` or `docs/RUNNING.md`.
- Update the idea/program state if implementation meaningfully changes project status.

## Implementation order

1. Add normalization layer.
2. Add derived topology builder.
3. Add benchmark dataset and runner.
4. Add keyword + recency baselines.
5. Add topology-aware hybrid scoring.
6. Add CLI affordances.
7. Add docs and end-to-end validation.

## Definition of done

This is done when:
- retrieval works over live Ygg continuity surfaces,
- benchmark cases run cleanly,
- the topology-aware strategy is explainable,
- CLI exposure is usable,
- tests pass,
- and the feature is documented well enough for repeatable use.

## Notes

This plan intentionally starts with a derived topology over existing state instead of introducing a new authoritative topology file.
