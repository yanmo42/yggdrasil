#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
YGG_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"

CONTRACT_PATH="${YGG_PATHS_FILE:-}"
SPINE_ROOT_OVERRIDE=""
BACKUP_FILE=""
BACKUP_DIR="${YGG_BACKUP_DIR:-$YGG_ROOT/state/runtime/backups}"
KEY_FILE="${YGG_BACKUP_KEY_FILE:-$HOME/.config/ygg/backup.key}"
RESTORE_TO=""
IN_PLACE=0
FORCE=0

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Restore an encrypted spine backup archive.

Options:
  --backup FILE       Backup file to restore (default: latest in backup dir)
  --backup-dir DIR    Backup directory (default: $BACKUP_DIR)
  --contract PATH     Path contract file override
  --spine-root PATH   Explicit spine root override
  --key-file PATH     Encryption key file (default: $KEY_FILE)
  --to DIR            Restore to target directory (default: state/runtime/restore-<ts>)
  --in-place          Restore into current spine root (requires --force)
  --force             Required when restoring into a non-empty dir or in-place
  -h, --help          Show help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --backup)
      BACKUP_FILE="$2"
      shift 2
      ;;
    --backup-dir)
      BACKUP_DIR="$2"
      shift 2
      ;;
    --contract)
      CONTRACT_PATH="$2"
      shift 2
      ;;
    --spine-root)
      SPINE_ROOT_OVERRIDE="$2"
      shift 2
      ;;
    --key-file)
      KEY_FILE="$2"
      shift 2
      ;;
    --to)
      RESTORE_TO="$2"
      shift 2
      ;;
    --in-place)
      IN_PLACE=1
      shift
      ;;
    --force)
      FORCE=1
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

if ! command -v openssl >/dev/null 2>&1; then
  echo "openssl is required for decryption" >&2
  exit 1
fi

resolve_spine_root() {
  local contract="${1:-}"
  local ygg_root="$2"

  python3 - "$ygg_root" "$contract" <<'PY'
import sys
from pathlib import Path

ygg_root = Path(sys.argv[1]).expanduser().resolve()
contract = (sys.argv[2] or "").strip()

sys.path.insert(0, str(ygg_root / "code" / "src"))
from path_contract import resolve_runtime_paths  # type: ignore

rt = resolve_runtime_paths(contract or None)
print(rt.spine_root)
PY
}

if [[ -n "$SPINE_ROOT_OVERRIDE" ]]; then
  SPINE_ROOT="$(cd "$SPINE_ROOT_OVERRIDE" && pwd)"
else
  SPINE_ROOT="$(resolve_spine_root "$CONTRACT_PATH" "$YGG_ROOT")"
fi

if [[ -z "$BACKUP_FILE" ]]; then
  BACKUP_FILE="$(ls -1t "$BACKUP_DIR"/spine-*.tar.gz.enc 2>/dev/null | head -n 1 || true)"
fi

if [[ -z "$BACKUP_FILE" || ! -f "$BACKUP_FILE" ]]; then
  echo "Backup file not found. Provide --backup or ensure $BACKUP_DIR has archives." >&2
  exit 1
fi

if [[ ! -f "$KEY_FILE" ]]; then
  echo "Backup key file missing: $KEY_FILE" >&2
  exit 1
fi

if [[ "$IN_PLACE" -eq 1 ]]; then
  if [[ "$FORCE" -ne 1 ]]; then
    echo "--in-place requires --force" >&2
    exit 1
  fi
  TARGET_DIR="$SPINE_ROOT"
else
  if [[ -z "$RESTORE_TO" ]]; then
    STAMP="$(date +%Y%m%d-%H%M%S)"
    TARGET_DIR="$YGG_ROOT/state/runtime/restore-$STAMP"
  else
    TARGET_DIR="$RESTORE_TO"
  fi
fi

mkdir -p "$TARGET_DIR"

if [[ -n "$(find "$TARGET_DIR" -mindepth 1 -maxdepth 1 2>/dev/null | head -n 1)" && "$FORCE" -ne 1 ]]; then
  echo "Target directory is not empty: $TARGET_DIR (use --force)" >&2
  exit 1
fi

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

PLAIN_TAR="$TMP_DIR/restore.tar.gz"

echo "decrypting: $BACKUP_FILE"
openssl enc -d -aes-256-cbc -pbkdf2 -in "$BACKUP_FILE" -out "$PLAIN_TAR" -pass file:"$KEY_FILE"

echo "extracting into: $TARGET_DIR"
tar -xzf "$PLAIN_TAR" -C "$TARGET_DIR"

echo "restore complete"
echo "target: $TARGET_DIR"
echo "next: $YGG_ROOT/state/scripts/verify-restore.sh --path $TARGET_DIR"
