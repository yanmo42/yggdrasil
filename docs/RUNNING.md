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

```bash
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

```bash
ygg forge --domain website-dev --task theme-selector-enhancements \
  "implement the improved theme selector UX"
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
ygg raven launch --trigger heartbeat "scan env" --json
ygg raven status --json
ygg graft propose "Add proposal gate" --json
ygg beak propose "Mark stale branch" --json
ygg root --print-packet "help me plan"
ygg resume website-dev theme-selector-enhancements --print-only
ygg branch demo-domain demo-task --dry-run
ygg forge --domain website-dev --task theme-selector-enhancements --print-packet
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
- `ygg forge` biases planner routing toward implementation; it does not directly spawn codex by itself yet
