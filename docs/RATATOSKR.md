# RATATOSKR — Continuity Courier

If Heimdall sees, Ratatoskr carries.

**Ownership class: `bridge`**
Ratatoskr is a bridge surface. It carries ygg-canonical events into assistant-local note sinks
without claiming ownership of those sinks. It does not mutate ygg-canonical state.
See `docs/BRIDGE-OWNERSHIP-CONTRACT.md` for the full ownership class model.

## Role

Ratatoskr routes small structured continuity events to:
- daily continuity notes
- promotion-candidate queue

## Event shape (v1)

```json
{
  "kind": "runtime-refresh",
  "source": "heimdall",
  "summary": "Runtime embodiment changed",
  "importance": "important",
  "details": {
    "changes": [{"field": "model", "old": "x", "new": "y"}],
    "fingerprint": "abcd1234"
  },
  "route": {
    "daily": true,
    "promote": false,
    "notify": false
  }
}
```

## Routing defaults

- Daily note write when `route.daily=true`
- Promotion-candidate write when `route.promote=true`
- No notification fan-out by default in v1

## Current ygg v1 files

- Daily notes: `state/notes/daily/YYYY-MM-DD.md`
- Promotion candidates: `state/runtime/promotion-candidates.jsonl`
