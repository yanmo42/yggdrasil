#!/usr/bin/env bash
set -euo pipefail

# One-command host bootstrap for Ygg/OpenClaw topology.
# Safe defaults: idempotent, non-destructive, and configurable via env/flags.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_WORKSPACE_ROOT="$HOME/.openclaw/workspace-claw-main"
DEFAULT_YGG_ROOT="$HOME/ygg"
DEFAULT_PROJECTS_ROOT="$HOME/projects"
DEFAULT_SANDY_ROOT="$DEFAULT_PROJECTS_ROOT/sandy-chaos"
DEFAULT_SITE_ROOT="$DEFAULT_PROJECTS_ROOT/ianmoog-site"

WORKSPACE_ROOT="${WORKSPACE_ROOT:-$DEFAULT_WORKSPACE_ROOT}"
YGG_ROOT="${YGG_ROOT:-$DEFAULT_YGG_ROOT}"
PROJECTS_ROOT="${PROJECTS_ROOT:-$DEFAULT_PROJECTS_ROOT}"
SANDY_ROOT="${SANDY_ROOT:-$DEFAULT_SANDY_ROOT}"
SITE_ROOT="${SITE_ROOT:-$DEFAULT_SITE_ROOT}"

SPINE_GIT_URL="${SPINE_GIT_URL:-}"
YGG_GIT_URL="${YGG_GIT_URL:-}"
SANDY_CHAOS_GIT_URL="${SANDY_CHAOS_GIT_URL:-}"
IANMOOG_SITE_GIT_URL="${IANMOOG_SITE_GIT_URL:-}"

DRY_RUN=0
SKIP_INSTALL=0
SKIP_OPENCLAW_INSTALL=0
REWRITE_PATH_CONTRACT=0

log() {
  printf '%s\n' "$*"
}

warn() {
  printf 'WARN: %s\n' "$*" >&2
}

run_cmd() {
  log "+ $*"
  if [[ "$DRY_RUN" -eq 0 ]]; then
    "$@"
  fi
}

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Options:
  --dry-run                 Print actions without executing
  --skip-install            Skip OS package install phase
  --skip-openclaw-install   Skip OpenClaw install check/install
  --rewrite-path-contract   Overwrite existing ygg-paths.yaml
  --workspace-root PATH     Override workspace root (default: $DEFAULT_WORKSPACE_ROOT)
  --ygg-root PATH           Override ygg root (default: $DEFAULT_YGG_ROOT)
  --projects-root PATH      Override projects root (default: $DEFAULT_PROJECTS_ROOT)
  -h, --help                Show this help

Env overrides (optional):
  SPINE_GIT_URL, YGG_GIT_URL, SANDY_CHAOS_GIT_URL, IANMOOG_SITE_GIT_URL
  WORKSPACE_ROOT, YGG_ROOT, PROJECTS_ROOT, SANDY_ROOT, SITE_ROOT

Examples:
  $(basename "$0")
  $(basename "$0") --dry-run
  SPINE_GIT_URL=git@github.com:you/openclaw-workspace.git \
  YGG_GIT_URL=git@github.com:you/ygg.git \
  $(basename "$0")
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --skip-install)
      SKIP_INSTALL=1
      shift
      ;;
    --skip-openclaw-install)
      SKIP_OPENCLAW_INSTALL=1
      shift
      ;;
    --rewrite-path-contract)
      REWRITE_PATH_CONTRACT=1
      shift
      ;;
    --workspace-root)
      WORKSPACE_ROOT="$2"
      shift 2
      ;;
    --ygg-root)
      YGG_ROOT="$2"
      shift 2
      ;;
    --projects-root)
      PROJECTS_ROOT="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      warn "Unknown option: $1"
      usage
      exit 2
      ;;
  esac
done

SANDY_ROOT="${SANDY_ROOT:-$PROJECTS_ROOT/sandy-chaos}"
SITE_ROOT="${SITE_ROOT:-$PROJECTS_ROOT/ianmoog-site}"
PATH_CONTRACT_FILE="$WORKSPACE_ROOT/config/ygg-paths.yaml"

detect_pkg_manager() {
  if command -v pacman >/dev/null 2>&1; then
    echo pacman
    return
  fi
  if command -v apt-get >/dev/null 2>&1; then
    echo apt
    return
  fi
  if command -v dnf >/dev/null 2>&1; then
    echo dnf
    return
  fi
  if command -v brew >/dev/null 2>&1; then
    echo brew
    return
  fi
  echo none
}

install_base_packages() {
  local mgr="$1"

  case "$mgr" in
    pacman)
      run_cmd sudo pacman -Sy --needed git curl jq rsync python python-pip nodejs npm
      ;;
    apt)
      run_cmd sudo apt-get update
      run_cmd sudo apt-get install -y git curl jq rsync python3 python3-pip nodejs npm
      ;;
    dnf)
      run_cmd sudo dnf install -y git curl jq rsync python3 python3-pip nodejs npm
      ;;
    brew)
      run_cmd brew install git curl jq rsync python node
      ;;
    *)
      warn "No supported package manager found; skipping install phase"
      ;;
  esac
}

ensure_openclaw_installed() {
  if command -v openclaw >/dev/null 2>&1; then
    log "openclaw already installed"
    return
  fi

  if [[ "$SKIP_OPENCLAW_INSTALL" -eq 1 ]]; then
    warn "openclaw is missing and install is skipped"
    return
  fi

  if ! command -v npm >/dev/null 2>&1; then
    warn "npm not available; cannot auto-install openclaw"
    return
  fi

  local prefix="${NPM_PREFIX:-$HOME/.npm-global}"
  run_cmd mkdir -p "$prefix"
  run_cmd npm config set prefix "$prefix"

  # Ensure current shell can find the newly installed binary.
  export PATH="$prefix/bin:$PATH"
  run_cmd npm install -g openclaw
}

clone_or_pull() {
  local url="$1"
  local dest="$2"
  local label="$3"

  if [[ -z "$url" ]]; then
    log "skip $label (no URL provided)"
    return
  fi

  if [[ -d "$dest/.git" ]]; then
    run_cmd git -C "$dest" pull --ff-only
    return
  fi

  if [[ -e "$dest" ]]; then
    warn "$label target exists but is not a git checkout: $dest"
    return
  fi

  run_cmd git clone "$url" "$dest"
}

write_path_contract() {
  if [[ -f "$PATH_CONTRACT_FILE" && "$REWRITE_PATH_CONTRACT" -ne 1 ]]; then
    log "path contract already exists: $PATH_CONTRACT_FILE"
    return
  fi

  run_cmd mkdir -p "$(dirname "$PATH_CONTRACT_FILE")"

  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "+ write $PATH_CONTRACT_FILE"
    return
  fi

  cat > "$PATH_CONTRACT_FILE" <<EOF
schema: ygg-paths/v1
profile: bootstrap-generated
updated_on: $(date +%F)

paths:
  spine:
    root: $WORKSPACE_ROOT
    config_dir: $WORKSPACE_ROOT/config
    memory_dir: $WORKSPACE_ROOT/memory
    backups_dir: $WORKSPACE_ROOT/backups

  control_plane:
    name: ygg
    root: $YGG_ROOT
    bin: $YGG_ROOT/bin/ygg

  work_repos:
    root: $PROJECTS_ROOT
    sandy-chaos: $SANDY_ROOT
    ianmoog-site: $SITE_ROOT

contracts:
  canonical_state_owner: spine
  canonical_path_registry: $PATH_CONTRACT_FILE
  branch_backflow: "Durable outcomes from repos should be promoted back into spine memory/state."
EOF
}

wire_ygg_bin() {
  local ygg_bin="$YGG_ROOT/bin/ygg"
  if [[ ! -f "$ygg_bin" ]]; then
    warn "ygg binary not found at $ygg_bin (skip symlink wiring)"
    return
  fi

  run_cmd mkdir -p "$HOME/.local/bin"
  run_cmd ln -sfn "$ygg_bin" "$HOME/.local/bin/ygg"
}

run_path_checks() {
  local ygg_cli_py="$YGG_ROOT/src/cli.py"

  if [[ -x "$HOME/.local/bin/ygg" ]]; then
    run_cmd "$HOME/.local/bin/ygg" paths check
    return
  fi

  if [[ -f "$ygg_cli_py" ]]; then
    run_cmd python3 "$ygg_cli_py" paths check
    return
  fi

  warn "Unable to run ygg path checks (no ygg executable found)"
}

main() {
  log "== Ygg/OpenClaw Host Bootstrap =="
  log "workspace: $WORKSPACE_ROOT"
  log "ygg root:  $YGG_ROOT"
  log "projects:  $PROJECTS_ROOT"
  log

  run_cmd mkdir -p "$WORKSPACE_ROOT" "$YGG_ROOT" "$PROJECTS_ROOT"

  if [[ "$SKIP_INSTALL" -ne 1 ]]; then
    local pkg_mgr
    pkg_mgr="$(detect_pkg_manager)"
    install_base_packages "$pkg_mgr"
  else
    log "skip package installation"
  fi

  ensure_openclaw_installed

  clone_or_pull "$SPINE_GIT_URL" "$WORKSPACE_ROOT" "spine workspace"
  clone_or_pull "$YGG_GIT_URL" "$YGG_ROOT" "ygg"
  clone_or_pull "$SANDY_CHAOS_GIT_URL" "$SANDY_ROOT" "sandy-chaos"
  clone_or_pull "$IANMOOG_SITE_GIT_URL" "$SITE_ROOT" "ianmoog-site"

  write_path_contract
  wire_ygg_bin
  run_path_checks

  log
  log "Bootstrap complete."
  log "Next:"
  log "  1) Ensure PATH includes ~/.local/bin"
  log "  2) Run: ygg paths"
  log "  3) Run: ygg status"
}

main "$@"
