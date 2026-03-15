# State Package

This package defines the state boundary for portability.

- `templates/` → checked-in templates (safe)
- `policy/` → checked-in policy docs (safe)
- `scripts/` → backup/restore tooling (safe)
- `runtime/` → generated runtime outputs (ignored)
- `notes/` → generated operational notes (ignored)

## Scripts

```bash
~/ygg/state/scripts/new-backup-key.sh
~/ygg/state/scripts/spine-backup.sh
~/ygg/state/scripts/spine-restore.sh
~/ygg/state/scripts/verify-restore.sh
```

Never commit raw secrets, credentials, or unencrypted session/state dumps.
