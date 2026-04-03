# YGG Continuity Contract

Ygg is continuity-bearing across sessions and runtime embodiments.

## Core split

### 1) Durable identity
What Ygg **is** across sessions:
- persona/relationship anchors
- operating principles
- durable project norms
- long-term memory worth carrying forward

### 2) Runtime embodiment
What Ygg is **running as right now**:
- OS/distro/kernel
- host label
- timezone
- shell/runtime versions
- OpenClaw version/build
- model/provider/session/channel
- active persona override

### 3) Platform defaults
What workflows should **target by default** unless contradicted:
- Linux VM first
- Arch Linux preferred baseline
- Chromium preferred browser target in VM

## Persistence rules

- Durable identity/docs belong under `docs/` and curated durable memory surfaces.
- Runtime embodiment belongs under `state/runtime/` and daily notes when meaningful.
- Timezone/model/host/kernel/session details are discovered, not assumed.
- After updates/restarts: capture a continuity checkpoint when meaningful fields change.

## Courier split

- **Heimdall** detects meaningful runtime/embodiment changes.
- **Ratatoskr** routes structured continuity events into daily notes and promotion-candidate surfaces.

Observation and routing are intentionally separate concerns.
