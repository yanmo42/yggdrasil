# Ygg Commands Surface

This directory is the **topological command surface** for Ygg.

It exists so the filesystem reflects the conceptual vocabulary of the system:

- `raven/`
- `graft/`
- `beak/`
- `spine/`

## Important rule

These are **thin executable wrappers**, not a second implementation stack.

Canonical behavior lives in:

- `~/ygg/bin/ygg`
- `~/ygg/lib/ygg/`

The scripts here should stay:

- small
- legible
- stable in path shape
- faithful to the canonical CLI

## Why keep this directory

Because Ygg is organized around command families and roles, not just around Python modules.
A top-level `commands/` tree makes that architecture visible.

## Failure condition

If a script in `commands/` starts carrying its own state model, parsing logic, or behavior that diverges from `bin/ygg`, the architecture is drifting.
