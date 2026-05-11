# Running Ygg

This file explains how to run the Ygg CLI in its current v1 shape.

## Command name

The CLI namespace is:

```bash
ygg
```

## How it is exposed on this machine

The executable is available through a symlink in:

```bash
~/.local/bin/ygg
```

That symlink points to:

```bash
~/ygg/bin/ygg
```

Because `~/.local/bin` is on the shell `PATH`, you can run:

```bash
ygg --help
ygg status
```

from anywhere.

## User-level systemd on Arch

Ygg now ships a first user-level systemd path for Arch-style machines.
The intended surface is:

- tracked templates in `~/ygg/machine/systemd/user/`
- rendered units in `~/.config/systemd/user/`
- current useful unit: `ygg-heimdall.service` with `ygg-heimdall.timer`

This stays inside the local user account instead of assuming a root-owned global service.

### Install the units

```bash
~/ygg/machine/install-systemd-user-units.sh
systemctl --user daemon-reload
```

Or do it as part of host bootstrap:

```bash
~/ygg/machine/bootstrap-host.sh --profile stable --install-user-units
```

### Enable the timer

```bash
~/ygg/machine/install-systemd-user-units.sh --enable-timers
systemctl --user status ygg-heimdall.timer
systemctl --user list-timers ygg-heimdall.timer
```

The timer runs:

```bash
ygg heimdall --workspace ~/ygg --note --ratatoskr
```

That gives Ygg a portable user-session refresh loop without making system boot depend on a root service.

## Morning restart ritual

After a reboot or full OpenClaw restart, the canonical single-command re-entry path is:

```bash
ygg wake
```

`ygg wake` intentionally crosses the boundary between OpenClaw runtime health and Ygg continuity state. It runs the practical morning flush in one pass:
- `openclaw status`
- Ygg repo status
- `ygg heimdall --note --ratatoskr`
- `ygg frontier current`
- `ygg frontier open`
- Sandy Chaos repo status

Use `ygg wake --print-only` if you want to inspect the ritual without launching it.

### Arch note

If you want user timers to run without an active login session, enable lingering for the operator account:

```bash
loginctl enable-linger "$USER"
```

## Important filesystem detail

`~/.local/bin/ygg` is a **symlink**, not a copy.

That means:

- editing `~/ygg/bin/ygg` changes what `ygg` runs
- removing the symlink from `~/.local/bin/ygg` does **not** delete `~/ygg/bin/ygg`

## Current source-of-truth split

Right now Ygg is a thin control surface over the current assistant-home implementation.

### Human-facing Ygg home

- `~/ygg/README.md`
- `~/ygg/docs/`
- `~/ygg/lib/ygg/cli.py`
- `~/ygg/bin/ygg` (compat launcher)
- `~/ygg/machine/bootstrap-host.sh`

### Current authoritative implementation

- `~/.openclaw/workspace-claw-main/scripts/work.py`
- `~/.openclaw/workspace-claw-main/scripts/resume.py`
- `~/.openclaw/workspace-claw-main/tools/work_v1/`
- `~/.openclaw/workspace-claw-main/state/resume/`

This means Ygg is the clean front door, while some implementation still lives in the assistant workspace.

For the explicit ownership boundary, read:

- `docs/DEPENDENCIES.md`
- `links/README.md`

## Core commands

## Operator stance

The intended shape is:
- humans should usually be able to start with `ygg work`
- explicit verbs should remain available for precision, scripting, debugging, and machine-to-machine routing
- natural language should reduce command burden at the surface
- deterministic structured routing should remain visible underneath

### Explain what verbs do (self-teaching)

```bash
ygg explain
ygg explain suggest
ygg help promote
ygg explain promote --json
```

### Ask Ygg what command it suggests

```bash
ygg suggest "implement the improved theme selector UX"
ygg suggest --domain website-dev --task theme-selector-enhancements \
  "implement the improved theme selector UX"
```

### Inspect status

```bash
ygg status
ygg status website-dev
```

### Switch persona mode override

```bash
ygg mode nyx
ygg mode solace
ygg mode get
ygg mode clear
ygg mode nyx --session planner--main
ygg mode nyx --no-notify
```

`ygg mode` is a Ygg-side control for persona posture, not a native OpenClaw engine switch.
It persists override state to both:
- `~/ygg/state/runtime/persona-mode.json`
- `~/.openclaw/workspace-claw-main/state/persona-mode.json`

By default it also sends a live switch directive into the target session. Use `--no-notify` if you only want to persist state.

### Inspect/validate path contract

```bash
ygg paths
ygg paths check
ygg paths check --json
```

### Inventory the repo itself

```bash
ygg inventory
ygg inventory --json
ygg inventory --root ~/ygg
```

### Inspect semantic program and idea registries

```bash
ygg program list
ygg program show ygg-continuity-integration
ygg program list --json
ygg idea list
ygg idea show topology-aware-continuity-retrieval
ygg idea list --json
```

### Query continuity state across surfaces

```bash
ygg retrieve "topology-aware continuity retrieval"
ygg retrieve "runtime embodiment changed" --strategy recency --explain
ygg retrieve --json "continuity integration"
ygg retrieve-benchmark
ygg retrieve-benchmark --json
```

`ygg retrieve` queries one normalized corpus built from:
- `state/ygg/checkpoints/`
- `state/ygg/ideas.json`
- `state/ygg/programs.json`
- `state/runtime/event-queue.jsonl`
- `state/runtime/promotions.jsonl`

The retrieval strategies are:
- `keyword`
- `recency`
- `topology`

The topology strategy derives inspectable graph links from the normalized records at query time. It does not require a canonical `state/ygg/topology.json`.

### Run RAVENS v1 flights

```bash
ygg raven launch --trigger human-request "Inspect package boundary drift"
ygg raven status
ygg raven inspect <flight-id>
ygg raven return <flight-id>
ygg raven adjudicate <flight-id> ADOPT
```

### Use topology-aligned command wrappers (optional)

These wrapper paths are intentionally thin front doors into the canonical Ygg implementation:

```bash
./commands/raven/launch --trigger human-request "Inspect package boundary drift"
./commands/raven/return <flight-id> --recommendation "Review result"
./commands/spine/adjudicate/adjudicate <flight-id> ADOPT
./commands/graft/propose "Add proposal gate" --target-attachment state/policy/
./commands/beak/propose "Deprecate duplicate docs" --target docs/ --problem-type duplication
```

### Propose growth/pruning artifacts

```bash
ygg graft propose "Add proposal gate" --target-attachment state/policy/
ygg beak propose "Deprecate duplicate docs" --target docs/ --problem-type duplication
```

### Enter planner/work front door

This should increasingly be the default human entrypoint.

```bash
ygg work
ygg work "add more functionality to theme selector in personal website"
```

### Force planner root/spine

```bash
ygg root "help me decide the next move"
```

### Create or refresh a branch

```bash
ygg branch website-dev theme-selector-enhancements \
  --objective "Add more functionality to the theme selector" \
  --next-action "Inspect current website implementation"
```

### Resume a lane

```bash
ygg resume website-dev theme-selector-enhancements
```

### Bias toward implementation/delegation

Use this when you want an explicit execution-oriented control.
If you're not sure, prefer `ygg work` and let the front door resolve posture.

```bash
ygg forge --domain website-dev --task theme-selector-enhancements \
  "implement the improved theme selector UX"

# print a ready-to-run Codex command with wake behavior baked in
ygg forge --domain ygg-dev --task sandy-chaos-alignment-constraints-v1 \
  --print-worker-command --wake-now
```

### Record a branch disposition

```bash
ygg promote website-dev theme-selector-enhancements \
  --disposition log-daily \
  --note "Scope clarified and ready for build"
```

## Safe preview modes

Several verbs support non-mutating inspection modes:

```bash
ygg suggest "implement the improved theme selector UX"
ygg suggest --json "implement the improved theme selector UX"
ygg help suggest --json
ygg inventory --json
ygg program list --json
ygg idea list --json
ygg retrieve --json "runtime embodiment changed"
ygg retrieve-benchmark --json
ygg raven launch --trigger heartbeat "scan env" --json
ygg raven status --json
ygg graft propose "Add proposal gate" --json
ygg beak propose "Mark stale branch" --json
ygg root --print-packet "help me plan"
ygg resume website-dev theme-selector-enhancements --print-only
ygg branch demo-domain demo-task --dry-run
ygg forge --domain website-dev --task theme-selector-enhancements --print-packet
ygg forge --domain ygg-dev --task sandy-chaos-alignment-constraints-v1 --print-worker-command --wake-now
ygg promote website-dev theme-selector-enhancements --disposition log-daily --dry-run
```

## Contract smoke checks

If you modify verb semantics or `ygg help/explain` payload shape:

```bash
python3 -m unittest discover -s ~/ygg/tests -p 'test_*.py' -v
```

## When changes take effect

Changes to Ygg usually take effect immediately because `ygg` resolves to `~/ygg/bin/ygg`, which executes `python3 -m ygg.cli` with `~/ygg/lib` on `PYTHONPATH`.

In some shells, command-location caching may need a refresh after replacing executables:

```bash
hash -r
```

Opening a new shell also works.

## Documentation index

Read these in order if you want the full model:

1. `~/ygg/README.md`
2. `~/ygg/docs/NORTH-STAR.md`
3. `~/ygg/docs/RAVENS.md`
4. `~/ygg/docs/RAVENS-V1.md`
5. `~/ygg/docs/VOCAB.md`
6. `~/ygg/docs/VERBS.md`
7. `~/ygg/docs/CONTRACTS.md`
8. `~/ygg/docs/CONTINUITY-OPS-V1.md`
9. `~/ygg/docs/ARCHITECTURE.md`
10. `~/ygg/docs/ROADMAP.md`
11. `~/ygg/SECURITY.md`

## v1 limitations

- some underlying implementation still lives in `~/.openclaw/workspace-claw-main`
- `ygg promote --disposition promote-durable` records a durable-promotion event but does not yet auto-rewrite canonical long-term memory/policy files
- `ygg forge` still does not directly spawn codex by itself yet, but it can now print the exact worker command to run next via `--print-worker-command` (optionally with `--wake-now`)
