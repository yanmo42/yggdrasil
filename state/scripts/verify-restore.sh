#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
YGG_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"

TARGET_PATH=""
RUN_PACKET_TEST=1

usage() {
  cat <<EOF
Usage: $(basename "$0") --path DIR [options]

Verify a restored spine directory for minimum continuity readiness.

Options:
  --path DIR          Restored spine path to validate
  --no-packet-test    Skip scripts/work.py --print smoke test
  -h, --help          Show help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --path)
      TARGET_PATH="$2"
      shift 2
      ;;
    --no-packet-test)
      RUN_PACKET_TEST=0
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

if [[ -z "$TARGET_PATH" ]]; then
  usage
  exit 2
fi

if [[ ! -d "$TARGET_PATH" ]]; then
  echo "restore path not found: $TARGET_PATH" >&2
  exit 1
fi

required_files=(
  "AGENTS.md"
  "SOUL.md"
  "USER.md"
  "core/AGENTS.md"
  "core/SOUL.md"
  "core/USER.md"
  "core/MEMORY.md"
  "memory"
  "scripts/work.py"
  "scripts/resume.py"
)

missing=0
for rel in "${required_files[@]}"; do
  if [[ ! -e "$TARGET_PATH/$rel" ]]; then
    echo "missing: $rel"
    missing=1
  fi
done

if [[ "$missing" -ne 0 ]]; then
  echo "verification failed: required files missing" >&2
  exit 1
fi

if [[ "$RUN_PACKET_TEST" -eq 1 ]]; then
  if [[ ! -x "$TARGET_PATH/scripts/work.py" ]]; then
    chmod +x "$TARGET_PATH/scripts/work.py" || true
  fi

  if ! python3 "$TARGET_PATH/scripts/work.py" --workspace "$TARGET_PATH" --print >/tmp/ygg-verify-packet.out 2>&1; then
    echo "verification failed: packet smoke test failed" >&2
    tail -n 40 /tmp/ygg-verify-packet.out || true
    exit 1
  fi

  if ! grep -q "Planner boot" /tmp/ygg-verify-packet.out; then
    echo "verification failed: packet output missing 'Planner boot'" >&2
    tail -n 40 /tmp/ygg-verify-packet.out || true
    exit 1
  fi
fi

echo "verify-restore: PASS"
echo "path: $TARGET_PATH"
