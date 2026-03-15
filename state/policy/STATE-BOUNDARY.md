# State Boundary Policy

## Purpose
Define what is portable/packageable in git versus what stays as runtime-only machine state.

## Safe to commit
- state/templates/*
- state/policy/*
- state/scripts/* (automation code, no secrets)
- encrypted backup artifacts metadata (not raw secrets)

## Never commit
- ~/.openclaw/credentials/
- ~/.openclaw/openclaw.json (unless fully redacted template)
- ~/.openclaw/agents/*/sessions/
- unencrypted memory dumps or token-bearing logs
- plaintext backup passphrases/keys

## Runtime outputs
Write generated runtime outputs under `state/runtime/`.
This folder is intentionally ignored by git.

## Principle
Code + machine setup are portable.
Live state is recoverable via controlled backup/restore, not by committing secrets.
