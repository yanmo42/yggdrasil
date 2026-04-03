# Kernelization Audit — 2026-04-02

## Decision

The current filesystem already contains the beginnings of the portable system.
The right move is **not** to fork an entire Arch Linux binary first.
The right move is to make **Ygg** the canonical, GitHub-managed control-plane repo, keep **TARA** as the protocol-contract repo, treat the OpenClaw workspace as the current runtime/spine owner, and extract only the portable pieces that improve clarity and repeatability.

In short:

- `~/ygg` should be the kernelized operator-facing base.
- `~/tara` should stay the contract/schema repo for cross-time handoff.
- `~/.openclaw/workspace-claw-main` should remain a runtime/private spine surface until specific modules are promoted.
- `~/projects/sandy-chaos` should be treated as an optional lab/benchmark repo, not as the OS kernel itself.

This audit was grounded in the observed machine state on **2026-04-02**.

---

## Observed nucleus

### 1. `~/ygg` is already acting like the portable base

Evidence:

- `README.md` defines Ygg as the **local operator-facing control plane**.
- `docs/ARCHITECTURE.md` and `docs/DEPENDENCIES.md` already define a clean ownership model.
- `machine/bootstrap-host.sh` is already the host bootstrap front door.
- `state/README.md` and `state/policy/STATE-BOUNDARY.md` already distinguish commit-safe state from runtime-only state.
- `state/templates/ygg-paths.yaml.template` and `state/templates/ygg-self.example.json` already look like the beginnings of a portable machine profile.

Decision:

- Treat `~/ygg` as the seed of the custom portable OS/toolkit.
- Expand it by extracting portable control-plane logic and machine bootstrap, not by absorbing every local runtime artifact.

### 2. `~/tara` is a real product boundary, not fluff

Evidence:

- Clean dedicated repo with schemas, examples, tools, and docs.
- The repo expresses a transport/continuity contract rather than ad hoc notes.

Decision:

- Keep `~/tara` separate and public-facing if desired.
- Treat it as the protocol layer that the portable OS can depend on.

### 3. `~/.openclaw/workspace-claw-main` is partly core, but not portable wholesale

Observed on **2026-04-02**:

- Git status: `main...origin/main [ahead 2]`
- Dirty/untracked continuity work present
- Owns current planner/resume/runtime machinery
- Contains new continuity artifacts (`Heimdall`, `Ratatoskr`, YGG docs) that look promotable

Decision:

- Do **not** GitHub-publish this whole tree as the portable OS.
- Keep it as the current runtime/private spine owner.
- Promote only the pieces that clearly belong to Ygg:
  - continuity docs
  - runtime refresh/courier logic
  - stable path/bootstrap contracts

### 4. `~/projects/sandy-chaos` is valuable, but optional to the OS base

Observed on **2026-04-02**:

- Real repo with tests, scripts, systemd units, and research workflow
- Dirty state present (`?? .codex`, `?? state/lux_nyx/`)
- Contains useful automation and benchmark surfaces

Decision:

- Keep as an optional attached lab.
- Reuse it for simulations, benchmarks, and agent workflow experiments.
- Do not make it part of the minimum portable kernel.

---

## Classification

### Promote into the kernelized base

- `~/ygg`
  Reason: already owns architecture, bootstrap, path contracts, state boundary, and the public operator surface.
- `~/tara`
  Reason: protocol/schema boundary is coherent, inspectable, and portable.
- `~/.zshrc`
  Reason: useful as a **template**, not as a literal committed file.
- `~/.gitconfig`
  Reason: useful as a template/overlay.
- `~/.config/starship.toml`
  Reason: portable operator UX layer.
- `~/.config/systemd/user`
  Reason: portable automation surface.

### Keep as optional attached repos/modules

- `~/projects/sandy-chaos`
  Reason: strong lab and benchmark surface; not required for the minimal OS kernel.
- `~/projects/nyx-nlp`
  Reason: optional library/project module, not part of the machine base.

### Keep as docs/distribution surfaces, not kernel

- `~/projects/ianmoog-site`
  Reason: outward-facing docs/publishing surface; useful for dissemination, not for bootstrapping the OS.

### Keep private/runtime-only

- `~/.openclaw/agents`
- `~/.openclaw/browser`
- `~/.openclaw/memory`
- `~/.openclaw/tasks`
- `~/.claude`
- `~/.codex`
- `~/.ollama`

Reason:

- these are live runtime surfaces, history stores, caches, auth state, or local model payloads
- they should be backed up or regenerated, not blindly pushed to GitHub

### Treat as disposable or reproducible

- `~/.cache`
- `~/.npm`
- `~/.npm-global`
- `~/.vscode-server`
- `~/.zcompdump`

Reason:

- these are reproducible caches/install surfaces, not source of truth

### Treat as legacy/archive surfaces

- `~/.openclaw/workspace-legacy`
- `~/projects/_assistant_home_legacy_20260307-203553`

Reason:

- these may contain useful history, but they should not define the future architecture

---

## Immediate blockers before GitHub kernelization

### 1. Secret handling is not ready yet

Observed directly:

- `~/.zshrc` contains plaintext API-key exports on **2026-04-02**
- other secret-bearing surfaces exist:
  - `~/.openclaw/openclaw.json`
  - `~/.codex/auth.json`
  - `~/.claude/.credentials.json`
  - `~/.config/gh/hosts.yml`
  - `~/.config/ygg/backup.key`

Required action:

- move secrets into env overlays, secret-manager inputs, or local-only files
- publish templates/examples only

### 2. Ownership is still split between Ygg and assistant-home

Current reality:

- Ygg is the clean control-plane shell
- OpenClaw workspace still owns planner/resume/runtime internals

Required action:

- keep the split explicit
- promote only modules with clear ownership
- do not fake self-containment by copying runtime machinery blindly

### 3. Arch packaging should come after profile hardening

Do not start with:

- a custom distro fork
- a monolithic "all my files are the OS" repo

Start with:

- Arch-first package manifest
- Ygg bootstrap script
- path contract template
- user-level systemd templates
- shell/profile templates
- clear private-runtime boundary

---

## Proposed GitHub topology

### Repo 1: `ygg`

Purpose:

- control plane
- bootstrap
- host inventory
- state policies
- portable operator UX
- continuity kernel

Should contain:

- `bin/`, `lib/`, `commands/`, `docs/`, `tests/`, `machine/`, `state/templates/`, `state/policy/`

Should not contain:

- live auth
- raw runtime DBs
- browser payloads
- transcripts/session dumps

### Repo 2: `tara`

Purpose:

- transport/continuity schemas
- examples
- validators

### Repo 3: private `openclaw-workspace` or `spine`

Purpose:

- planner runtime
- resume state
- private memory
- persona/runtime surfaces

### Repo 4: optional `sandy-chaos`

Purpose:

- research lab
- benchmark suite
- simulation/prototype playground

---

## Sequence that makes sense now

### Phase A — harden the portable base

1. Keep `~/ygg` as canonical.
2. Add inventory + manifest tooling.
3. Strip secret assumptions out of shell/bootstrap templates.

### Phase B — promote the clearly portable continuity layer

1. Move/promote `Heimdall` into `~/ygg`.
2. Move/promote `Ratatoskr` into `~/ygg`.
3. Promote continuity docs from assistant-home into Ygg docs.

### Phase C — define the Arch-first machine profile

1. Add package manifest(s) for Arch baseline.
2. Add dotfile templates instead of raw home-directory copies.
3. Add systemd-user unit templates and install helpers.
4. Make `bootstrap-host.sh` enough to rebuild a fresh VM.

### Phase D — only then consider a fuller distro artifact

Only after the above works repeatably should we explore:

- an installable image
- an Arch ISO/custom image
- a more opinionated portable binary/system package

---

## Bottom line

You are closer than it feels.
The filesystem does **not** say "build everything from scratch."
It says:

1. `ygg` is the portable kernel candidate.
2. `tara` is the portable protocol layer.
3. OpenClaw workspace is the current runtime owner.
4. everything else should be sorted into optional lab, docs surface, runtime state, cache, or archive.

That is enough to start a real GitHub-managed portable operating base right now.
