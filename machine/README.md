# Machine Package

Machine-level setup and host bootstrap scripts.

## Primary entrypoints

```bash
~/ygg/machine/bootstrap-host.sh
~/ygg/machine/inventory-host.py
~/ygg/machine/install-backup-cron.sh
```

`bootstrap-host.sh` is idempotent and can:
- install base dependencies,
- load `stable` / `dev` bootstrap profiles from `state/profiles/`,
- ensure OpenClaw is installed,
- clone/pull configured repos,
- write/update the path contract,
- wire the `ygg` launcher,
- run `ygg paths check`.

`inventory-host.py` emits a JSON host inventory to support kernelization and portability planning.

`install-backup-cron.sh` can:
- install a managed daily cron block for encrypted spine backups,
- remove that block via `--uninstall`.

For env-driven setup, use:
- `~/ygg/state/templates/bootstrap-host.env.example`

Examples:

```bash
~/ygg/machine/bootstrap-host.sh --profile stable
~/ygg/machine/bootstrap-host.sh --profile dev
~/ygg/machine/bootstrap-host.sh --dry-run --profile dev
```
