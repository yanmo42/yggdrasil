#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
YGG_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
TEMPLATE_DIR="$YGG_ROOT/machine/systemd/user"

INSTALL_DIR="${YGG_SYSTEMD_USER_DIR:-$HOME/.config/systemd/user}"
YGG_BIN="${YGG_SYSTEMD_YGG_BIN:-$HOME/.local/bin/ygg}"
ENABLE_TIMERS=0
UNINSTALL=0
DRY_RUN=0
SYSTEMCTL_BIN="${SYSTEMCTL_BIN:-systemctl}"
LOGINCTL_BIN="${LOGINCTL_BIN:-loginctl}"
WANT_RELOAD=1

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Install or remove Ygg user-level systemd units for the current user.

Options:
  --install-dir PATH   Unit install dir (default: $INSTALL_DIR)
  --ygg-bin PATH       Absolute ygg executable used by units (default: $YGG_BIN)
  --enable-timers      Enable installed timers after writing units
  --uninstall          Remove managed Ygg user units
  --no-reload          Skip \`systemctl --user daemon-reload\`
  --dry-run            Print actions without applying
  -h, --help           Show help
EOF
}

log() {
  printf '%s\n' "$*"
}

run_cmd() {
  log "+ $*"
  if [[ "$DRY_RUN" -eq 0 ]]; then
    "$@"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --install-dir)
      INSTALL_DIR="$2"
      shift 2
      ;;
    --ygg-bin)
      YGG_BIN="$2"
      shift 2
      ;;
    --enable-timers)
      ENABLE_TIMERS=1
      shift
      ;;
    --uninstall)
      UNINSTALL=1
      shift
      ;;
    --no-reload)
      WANT_RELOAD=0
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
      printf 'Unknown option: %s\n' "$1" >&2
      usage
      exit 2
      ;;
  esac
done

UNITS=(
  ygg-heimdall.service
  ygg-heimdall.timer
)

render_unit() {
  local template_path="$1"
  local output_path="$2"

  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "== $(basename "$output_path") =="
    sed \
      -e "s|@YGG_ROOT@|$YGG_ROOT|g" \
      -e "s|@YGG_BIN@|$YGG_BIN|g" \
      "$template_path"
    return
  fi

  sed \
    -e "s|@YGG_ROOT@|$YGG_ROOT|g" \
    -e "s|@YGG_BIN@|$YGG_BIN|g" \
    "$template_path" > "$output_path"
}

if [[ "$UNINSTALL" -eq 1 ]]; then
  for unit in "${UNITS[@]}"; do
    if [[ "$ENABLE_TIMERS" -eq 1 && "$unit" == *.timer ]]; then
      run_cmd "$SYSTEMCTL_BIN" --user disable --now "$unit"
    fi
    if [[ -e "$INSTALL_DIR/$unit" ]]; then
      run_cmd rm -f "$INSTALL_DIR/$unit"
    fi
  done
  if [[ "$WANT_RELOAD" -eq 1 ]]; then
    run_cmd "$SYSTEMCTL_BIN" --user daemon-reload
  fi
  log "Removed Ygg user units from $INSTALL_DIR"
  exit 0
fi

run_cmd mkdir -p "$INSTALL_DIR"

for unit in "${UNITS[@]}"; do
  render_unit "$TEMPLATE_DIR/$unit.in" "$INSTALL_DIR/$unit"
done

if [[ "$WANT_RELOAD" -eq 1 ]]; then
  run_cmd "$SYSTEMCTL_BIN" --user daemon-reload
fi

if [[ "$ENABLE_TIMERS" -eq 1 ]]; then
  run_cmd "$SYSTEMCTL_BIN" --user enable --now ygg-heimdall.timer
fi

log
log "Installed Ygg user units into $INSTALL_DIR"
log "Rendered from: $TEMPLATE_DIR"
log "Ygg binary: $YGG_BIN"
if command -v "$LOGINCTL_BIN" >/dev/null 2>&1; then
  log "Optional on Arch: $LOGINCTL_BIN enable-linger \"$USER\""
fi
