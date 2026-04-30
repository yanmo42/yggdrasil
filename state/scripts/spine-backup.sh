#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
YGG_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"

CONTRACT_PATH="${YGG_PATHS_FILE:-}"
SPINE_ROOT_OVERRIDE=""
OUT_DIR="${YGG_BACKUP_DIR:-$YGG_ROOT/state/runtime/backups}"
KEY_FILE="${YGG_BACKUP_KEY_FILE:-$HOME/.config/ygg/backup.key}"
KEEP_COUNT="${YGG_BACKUP_KEEP:-14}"
DRY_RUN=0
NO_PRUNE=0
QUIET=0

log() {
  if [[ "$QUIET" -eq 0 ]]; then
    printf '%s\n' "$*"
  fi
}

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Create an encrypted backup archive of the OpenClaw spine workspace.

Options:
  --contract PATH     Path contract file override (ygg-paths.yaml)
  --spine-root PATH   Explicit spine root override
  --out-dir PATH      Output directory (default: $OUT_DIR)
  --key-file PATH     Encryption key file (default: $KEY_FILE)
  --keep N            Keep latest N backups (default: $KEEP_COUNT)
  --no-prune          Do not prune old backups
  --quiet             Minimal output
  --dry-run           Print actions without writing
  -h, --help          Show help

Environment:
  YGG_PATHS_FILE      Contract path fallback
  YGG_BACKUP_KEY_FILE Key file path fallback
  YGG_BACKUP_DIR      Output directory fallback
  YGG_BACKUP_KEEP     Retention count fallback
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --contract)
      CONTRACT_PATH="$2"
      shift 2
      ;;
    --spine-root)
      SPINE_ROOT_OVERRIDE="$2"
      shift 2
      ;;
    --out-dir)
      OUT_DIR="$2"
      shift 2
      ;;
    --key-file)
      KEY_FILE="$2"
      shift 2
      ;;
    --keep)
      KEEP_COUNT="$2"
      shift 2
      ;;
    --no-prune)
      NO_PRUNE=1
      shift
      ;;
    --quiet)
      QUIET=1
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

if ! command -v openssl >/dev/null 2>&1; then
  echo "openssl is required for encryption" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required" >&2
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

sys.path.insert(0, str(ygg_root / "lib"))
from ygg.path_contract import resolve_runtime_paths  # type: ignore

rt = resolve_runtime_paths(contract or None)
print(rt.spine_root)
PY
}

if [[ -n "$SPINE_ROOT_OVERRIDE" ]]; then
  SPINE_ROOT="$(cd "$SPINE_ROOT_OVERRIDE" && pwd)"
else
  SPINE_ROOT="$(resolve_spine_root "$CONTRACT_PATH" "$YGG_ROOT")"
fi

if [[ ! -d "$SPINE_ROOT" ]]; then
  echo "Spine root not found: $SPINE_ROOT" >&2
  exit 1
fi

if [[ ! -f "$KEY_FILE" ]]; then
  echo "Backup key file missing: $KEY_FILE" >&2
  echo "Create it with: mkdir -p \"$(dirname "$KEY_FILE")\" && openssl rand -base64 48 > \"$KEY_FILE\" && chmod 600 \"$KEY_FILE\"" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

STAMP="$(date +%Y%m%d-%H%M%S)"
HOST_TAG="$(hostname -s 2>/dev/null || hostname || echo host)"
BASENAME="spine-${HOST_TAG}-${STAMP}"
ENC_FILE="$OUT_DIR/${BASENAME}.tar.gz.enc"
SHA_FILE="$ENC_FILE.sha256"
META_FILE="$ENC_FILE.meta.json"

log "spine root: $SPINE_ROOT"
log "output: $ENC_FILE"

if [[ "$DRY_RUN" -eq 1 ]]; then
  log "[dry-run] would create encrypted backup"
  exit 0
fi

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

PLAIN_TAR="$TMP_DIR/${BASENAME}.tar.gz"

tar -C "$SPINE_ROOT" -czf "$PLAIN_TAR" .
openssl enc -aes-256-cbc -pbkdf2 -salt -in "$PLAIN_TAR" -out "$ENC_FILE" -pass file:"$KEY_FILE"
sha256sum "$ENC_FILE" > "$SHA_FILE"

cat > "$META_FILE" <<EOF
{
  "created_at": "$(date -Is)",
  "host": "${HOST_TAG}",
  "spine_root": "${SPINE_ROOT}",
  "archive": "$(basename "$ENC_FILE")",
  "sha256": "$(cut -d' ' -f1 "$SHA_FILE")",
  "encryption": "openssl-aes-256-cbc-pbkdf2"
}
EOF

log "backup created: $ENC_FILE"
log "checksum: $SHA_FILE"
log "metadata: $META_FILE"

if [[ "$NO_PRUNE" -eq 0 ]]; then
  mapfile -t backups < <(ls -1t "$OUT_DIR"/spine-*.tar.gz.enc 2>/dev/null || true)
  if (( ${#backups[@]} > KEEP_COUNT )); then
    for old in "${backups[@]:KEEP_COUNT}"; do
      log "prune: $old"
      rm -f "$old" "$old.sha256" "$old.meta.json"
    done
  fi
fi
