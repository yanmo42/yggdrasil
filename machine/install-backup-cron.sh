#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
YGG_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"

SCHEDULE="${YGG_BACKUP_CRON_SCHEDULE:-15 3 * * *}"
KEY_FILE="${YGG_BACKUP_KEY_FILE:-$HOME/.config/ygg/backup.key}"
CONTRACT_PATH="${YGG_PATHS_FILE:-$HOME/.openclaw/workspace-claw-main/config/ygg-paths.yaml}"
LOG_FILE="${YGG_BACKUP_CRON_LOG:-$YGG_ROOT/state/runtime/cron-backup.log}"
UNINSTALL=0
DRY_RUN=0

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Install or remove a daily cron job for encrypted spine backups.

Options:
  --schedule "CRON"   Cron schedule (default: '$SCHEDULE')
  --key-file PATH      Backup key file path (default: $KEY_FILE)
  --contract PATH      ygg-paths contract path (default: $CONTRACT_PATH)
  --log-file PATH      Cron log path (default: $LOG_FILE)
  --uninstall          Remove the managed backup cron block
  --dry-run            Print resulting crontab without applying
  -h, --help           Show help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --schedule)
      SCHEDULE="$2"
      shift 2
      ;;
    --key-file)
      KEY_FILE="$2"
      shift 2
      ;;
    --contract)
      CONTRACT_PATH="$2"
      shift 2
      ;;
    --log-file)
      LOG_FILE="$2"
      shift 2
      ;;
    --uninstall)
      UNINSTALL=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 2
      ;;
  esac
done

mkdir -p "$(dirname "$LOG_FILE")"

BACKUP_CMD="$YGG_ROOT/state/scripts/spine-backup.sh --contract \"$CONTRACT_PATH\" --key-file \"$KEY_FILE\" --quiet"
CRON_LINE="$SCHEDULE YGG_BACKUP_KEY_FILE=\"$KEY_FILE\" $BACKUP_CMD >> \"$LOG_FILE\" 2>&1"

BEGIN_MARK="# BEGIN YGG-SPINE-BACKUP"
END_MARK="# END YGG-SPINE-BACKUP"

CURRENT_CRON="$(crontab -l 2>/dev/null || true)"
STRIPPED="$(printf '%s\n' "$CURRENT_CRON" | awk -v b="$BEGIN_MARK" -v e="$END_MARK" '
  $0==b {skip=1; next}
  $0==e {skip=0; next}
  skip!=1 {print}
')"

if [[ "$UNINSTALL" -eq 1 ]]; then
  NEW_CRON="$STRIPPED"
else
  BLOCK="$BEGIN_MARK
$CRON_LINE
$END_MARK"
  if [[ -n "$STRIPPED" ]]; then
    NEW_CRON="$STRIPPED
$BLOCK"
  else
    NEW_CRON="$BLOCK"
  fi
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "$NEW_CRON"
  exit 0
fi

printf '%s\n' "$NEW_CRON" | crontab -

if [[ "$UNINSTALL" -eq 1 ]]; then
  echo "Removed YGG backup cron block"
else
  echo "Installed YGG backup cron block"
  echo "Schedule: $SCHEDULE"
  echo "Log file: $LOG_FILE"
fi
