# YGG Operating Baseline

Default target environment:
- Linux VM
- Arch Linux preferred baseline
- Chromium preferred browser automation target in VM

This is a practical default, not identity.
If runtime inspection differs, record the difference instead of pretending the default changed.

## Runtime refresh rule

Use Heimdall when:
- after updates/restarts
- after host/session/model changes
- before writing continuity checkpoints

Typical command:

```bash
ygg heimdall --note --ratatoskr
```

Behavior:
- updates `state/runtime/ygg-self.json`
- computes runtime fingerprint + history
- appends kernel runtime events (`state/runtime/event-queue.jsonl`)
- updates kernel boot-state pointer (`state/runtime/ygg-kernel.json`)
- when `--note --ratatoskr`: routes daily continuity note via Ratatoskr
