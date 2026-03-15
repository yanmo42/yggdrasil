# Continuity Ops v1 (Winter Pass + Autophagology)

A concise operator runbook for applying continuity pressure without overcomplicating workflow.

Builds on:
- `AUTOPHAGOLOGY.md`
- `WINTER-PASS.md`

---

## 1) Goal

Keep active work lanes viable by defaulting to:
- explicit review,
- explicit disposition,
- explicit evidence.

No silent drift. No immortal stale lanes.

---

## 2) Review cadence

### Daily mini-pass (5–10 min)
Run once near end of day.

Trigger:
- normal daily closeout.

Scope:
- active tasks only.

### Weekly full Winter Pass (20–40 min)
Run once per week.

Trigger (any):
- weekly cadence,
- active lanes > 5,
- promotion backlog > 5,
- explicit operator request.

Scope:
- active + warm lanes,
- unresolved promotion candidates,
- stale lanes.

### Event-driven pass (ad hoc)
Run when a phase shift or major context change happens.

---

## 3) Decision rubric (fast)

For each lane/unit, score:
- signal: `none|weak|strong`
- staleness: `low|medium|high`
- validation debt: `low|medium|high`
- operator demand: `low|medium|high`

Default dispositions:
- `strong signal + low/medium staleness` -> `RENEW`
- `weak signal + medium staleness` -> `COMPACT` or `HIBERNATE`
- `none signal + high staleness` -> `DIGEST` then `TERMINATE`
- `high consequence ambiguity` -> `ESCALATE_HITL`
- `output changes policy/memory` -> `PROMOTE`

---

## 4) Required output artifact

Each pass must emit one record with:
- reviewed units,
- chosen disposition,
- reclaimed artifacts,
- next review date.

Recommended location:
- `~/ygg/notes/winter-pass/YYYY-MM-DD.md`

Minimal record template:

```yaml
pass_id: WINTER-YYYYMMDD-01
scope: daily-mini|weekly-full|event-driven
unit_ref: <domain/task or artifact>
signal: none|weak|strong
staleness: low|medium|high
validation_debt: low|medium|high
operator_demand: low|medium|high
disposition: RENEW|COMPACT|LATENTIZE|PROMOTE|MERGE|HIBERNATE|DIGEST|TERMINATE|ESCALATE_HITL
reclaimed_artifacts:
  - <path/ref>
next_review: <date>
notes: <short rationale>
```

---

## 5) Practical command flow (today)

1. Inspect state:
```bash
ygg status
```

2. Resume lane if needed for context:
```bash
ygg resume <domain> <task> --print-only
```

3. Record disposition for meaningful outcomes:
```bash
ygg promote <domain> <task> --disposition <...> --note "..."
```

4. If lane is done:
```bash
ygg promote <domain> <task> --disposition log-daily --finish --note "..."
```

---

## 6) Claim tiers

### Defensible now
- manual daily/weekly pass using existing `ygg status`, `ygg resume`, `ygg promote`.
- explicit pass record in notes.

### Plausible next
- automate reminders/checks via cron.
- add simple backlog counters to prompt Winter Pass.

### Speculative
- 2D/3D branch topology UI (including AR/VR overlays) for live continuity visualization.

---

## 7) Failure conditions

This runbook is failing if:
- passes are skipped repeatedly,
- records are too vague to justify decisions,
- stale lanes keep renewing without evidence,
- or pruning is so aggressive that useful continuity cannot accumulate.
