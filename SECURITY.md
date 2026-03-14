# SECURITY.md

Ygg is a local-first wrapper around planner/resume flows, but public repos can still leak sensitive context through surrounding artifacts.

This file defines practical guardrails.

---

## 1) Threat model (realistic)

### Lower-risk surfaces
- CLI wrapper code (`src/cli.py`, `bin/ygg`)
- verb docs and architecture notes

### Higher-risk surfaces
- local logs/state/history (`state/`, promotion logs)
- symlinks to private/local paths (`links/`)
- copied terminal output containing tokens/IDs
- future `.env` or secret config files
- machine-specific absolute paths/usernames

---

## 2) Never commit these

- API keys/tokens/passwords/secrets/private keys
- `.env`/secrets files
- local runtime state and logs
- absolute-path symlink folders
- private transcripts/chat dumps unless intentionally redacted

Current `.gitignore` already excludes key local-risk folders.

---

## 3) Pre-push safety checklist

Before pushing:

1. **Check staged files**
   ```bash
   git status --short
   git diff --cached
   ```

2. **Quick secret scan**
   ```bash
   rg -n --hidden --glob '!.git' \
     -e 'AKIA[0-9A-Z]{16}' \
     -e 'ghp_[A-Za-z0-9]{36}' \
     -e 'github_pat_[A-Za-z0-9_]{20,}' \
     -e 'BEGIN (RSA|OPENSSH|EC) PRIVATE KEY' \
     -e 'TOKEN|SECRET|PASSWORD|API_KEY|apikey'
   ```

3. **Path/symlink sanity**
   - ensure `links/` or other machine-local pointers are not staged
   - avoid publishing private usernames/hostnames unless intentional

4. **Public-readability check**
   - if this commit were tweeted, would anything be embarrassing/private?

---

## 4) If a secret is leaked (fast response)

1. Revoke/rotate the secret immediately
2. Remove from repo history if needed
3. Force-push cleaned history if policy allows
4. Document the incident and prevention change

> Rotation first, cleanup second.

---

## 5) Security as an iteration loop (your framing)

Use a 3-lens loop for each release/commit:

1. **Possible (could happen)**
   - enumerate plausible failure/leak modes
2. **Probable (will likely happen)**
   - rank top realistic failures in current workflow
3. **Present (what is true now)**
   - inspect current staged files/state and execute controls now

Then iterate quickly:

- imagine risk
- test controls
- ship small
- review outcomes
- tighten guardrails

This is the same discipline as Ygg routing:

- explicit state
- explicit decisions
- explicit promotion/disposition
- no silent meaningful outcomes

---

## 6) Policy stance

- Keep public repos clean by default.
- Prefer false positives over silent leaks.
- Automate checks where cheap, review manually where high impact.

Security is not perfection; it is repeated legible control under uncertainty.
