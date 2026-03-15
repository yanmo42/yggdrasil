# Machine Package

Machine-level setup and host bootstrap scripts.

## Primary entrypoints

```bash
~/ygg/machine/bootstrap-host.sh
~/ygg/machine/install-backup-cron.sh
```

`bootstrap-host.sh` is idempotent and can:
- install base dependencies,
- ensure OpenClaw is installed,
- clone/pull configured repos,
- write/update the path contract,
- wire the `ygg` launcher,
- run `ygg paths check`.

`install-backup-cron.sh` can:
- install a managed daily cron block for encrypted spine backups,
- remove that block via `--uninstall`.

For env-driven setup, use:
- `~/ygg/state/templates/bootstrap-host.env.example`
