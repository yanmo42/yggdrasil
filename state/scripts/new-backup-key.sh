#!/usr/bin/env bash
set -euo pipefail

KEY_FILE="${1:-${YGG_BACKUP_KEY_FILE:-$HOME/.config/ygg/backup.key}}"

mkdir -p "$(dirname "$KEY_FILE")"
if [[ -f "$KEY_FILE" ]]; then
  echo "key file already exists: $KEY_FILE" >&2
  exit 1
fi

openssl rand -base64 48 > "$KEY_FILE"
chmod 600 "$KEY_FILE"

echo "created key: $KEY_FILE"
