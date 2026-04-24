#!/usr/bin/env bash
set -euo pipefail

# One-command host bootstrap for Ygg/OpenClaw topology.
# Safe defaults: idempotent, non-destructive, and configurable via env/flags.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_YGG_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
PROFILE_DIR="$SCRIPT_YGG_ROOT/state/profiles"
RENDER_COMPONENTS_PY="$SCRIPT_YGG_ROOT/machine/render-components.py"
RENDER_PATH_CONTRACT_PY="$SCRIPT_YGG_ROOT/machine/render-path-contract.py"

DEFAULT_WORKSPACE_ROOT="$HOME/.openclaw/workspace-claw-main"
DEFAULT_YGG_ROOT="$HOME/ygg"
DEFAULT_TARA_ROOT="$HOME/tara"
DEFAULT_PROJECTS_ROOT="$HOME/projects"
DEFAULT_SANDY_ROOT="$DEFAULT_PROJECTS_ROOT/sandy-chaos"
DEFAULT_SITE_ROOT="$DEFAULT_PROJECTS_ROOT/ianmoog-site"
DEFAULT_BOOTSTRAP_PROFILE="stable"
DEFAULT_PACMAN_PACKAGES=(
  git
  curl
  jq
  rsync
  python
  python-pip
  nodejs
  npm
)

DRY_RUN=0
SKIP_INSTALL=0
SKIP_OPENCLAW_INSTALL=0
REWRITE_PATH_CONTRACT=0
PROFILE_NAME="${BOOTSTRAP_PROFILE:-$DEFAULT_BOOTSTRAP_PROFILE}"
PROFILE_FILE=""

CLI_WORKSPACE_ROOT=""
CLI_YGG_ROOT=""
CLI_TARA_ROOT=""
CLI_PROJECTS_ROOT=""

trim() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

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
  --profile NAME            Bootstrap profile name or path (default: $DEFAULT_BOOTSTRAP_PROFILE)
  --dry-run                 Print actions without executing
  --skip-install            Skip OS package install phase
  --skip-openclaw-install   Skip OpenClaw install check/install
  --rewrite-path-contract   Overwrite existing ygg-paths.yaml
  --workspace-root PATH     Override workspace root (default: $DEFAULT_WORKSPACE_ROOT)
  --ygg-root PATH           Override ygg root (default: $DEFAULT_YGG_ROOT)
  --tara-root PATH          Override tara root (default: $DEFAULT_TARA_ROOT)
  --projects-root PATH      Override projects root (default: $DEFAULT_PROJECTS_ROOT)
  -h, --help                Show this help

Env overrides (optional):
  BOOTSTRAP_PROFILE
  COMPONENT_REGISTRY_FILE
  SPINE_GIT_URL, YGG_GIT_URL, TARA_GIT_URL, SANDY_CHAOS_GIT_URL, IANMOOG_SITE_GIT_URL
  SPINE_GIT_REF, YGG_GIT_REF, TARA_GIT_REF, SANDY_CHAOS_GIT_REF, IANMOOG_SITE_GIT_REF
  ENABLE_SPINE, ENABLE_YGG, ENABLE_TARA, ENABLE_SANDY_CHAOS, ENABLE_IANMOOG_SITE
  WORKSPACE_ROOT, YGG_ROOT, TARA_ROOT, PROJECTS_ROOT, SANDY_ROOT, SITE_ROOT

Examples:
  $(basename "$0")
  $(basename "$0") --profile dev
  $(basename "$0") --dry-run --profile stable
  SPINE_GIT_URL=git@github.com:you/openclaw-workspace.git \
  YGG_GIT_URL=git@github.com:you/ygg.git \
  $(basename "$0")
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      PROFILE_NAME="$2"
      shift 2
      ;;
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
      CLI_WORKSPACE_ROOT="$2"
      shift 2
      ;;
    --ygg-root)
      CLI_YGG_ROOT="$2"
      shift 2
      ;;
    --tara-root)
      CLI_TARA_ROOT="$2"
      shift 2
      ;;
    --projects-root)
      CLI_PROJECTS_ROOT="$2"
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

resolve_profile_file() {
  local requested="$1"

  if [[ -z "$requested" ]]; then
    printf '%s/bootstrap-profile.%s.env' "$PROFILE_DIR" "$DEFAULT_BOOTSTRAP_PROFILE"
    return
  fi

  if [[ "$requested" == */* || "$requested" == .* ]]; then
    printf '%s' "$requested"
    return
  fi

  printf '%s/bootstrap-profile.%s.env' "$PROFILE_DIR" "$requested"
}

load_profile() {
  local requested="$1"
  local profile_file
  profile_file="$(resolve_profile_file "$requested")"

  if [[ ! -f "$profile_file" ]]; then
    warn "Bootstrap profile not found: $profile_file"
    exit 2
  fi

  # shellcheck disable=SC1090
  source "$profile_file"
  PROFILE_FILE="$profile_file"
  if [[ -n "${BOOTSTRAP_PROFILE_NAME:-}" ]]; then
    PROFILE_NAME="$BOOTSTRAP_PROFILE_NAME"
  elif [[ -n "$requested" ]]; then
    PROFILE_NAME="$requested"
  else
    PROFILE_NAME="$DEFAULT_BOOTSTRAP_PROFILE"
  fi
}

resolve_asset_path() {
  local raw="$1"
  if [[ "$raw" = /* ]]; then
    printf '%s' "$raw"
    return
  fi
  printf '%s/%s' "$SCRIPT_YGG_ROOT" "$raw"
}

append_unique() {
  local -n array_ref="$1"
  local candidate="$2"
  local existing
  for existing in "${array_ref[@]:-}"; do
    if [[ "$existing" == "$candidate" ]]; then
      return
    fi
  done
  array_ref+=("$candidate")
}

read_manifest_packages() {
  local target_name="$1"
  local -n target_ref="$target_name"
  shift

  local manifest raw line manifest_path
  for manifest in "$@"; do
    manifest_path="$(resolve_asset_path "$manifest")"
    if [[ ! -f "$manifest_path" ]]; then
      warn "Package manifest not found: $manifest_path"
      continue
    fi

    while IFS= read -r raw || [[ -n "$raw" ]]; do
      line="${raw%%#*}"
      line="$(trim "$line")"
      if [[ -z "$line" ]]; then
        continue
      fi
      append_unique "$target_name" "$line"
    done < "$manifest_path"
  done
}

load_profile "$PROFILE_NAME"

COMPONENT_REGISTRY_FILE="${COMPONENT_REGISTRY_FILE:-state/profiles/components.yaml}"
COMPONENT_REGISTRY_PATH="$(resolve_asset_path "$COMPONENT_REGISTRY_FILE")"
eval "$(python3 "$RENDER_COMPONENTS_PY" --registry "$COMPONENT_REGISTRY_PATH" --profile "$PROFILE_NAME")"

WORKSPACE_ROOT="${CLI_WORKSPACE_ROOT:-${WORKSPACE_ROOT:-$DEFAULT_WORKSPACE_ROOT}}"
YGG_ROOT="${CLI_YGG_ROOT:-${YGG_ROOT:-$DEFAULT_YGG_ROOT}}"
TARA_ROOT="${CLI_TARA_ROOT:-${TARA_ROOT:-$DEFAULT_TARA_ROOT}}"
PROJECTS_ROOT="${CLI_PROJECTS_ROOT:-${PROJECTS_ROOT:-$DEFAULT_PROJECTS_ROOT}}"
SANDY_ROOT="${SANDY_ROOT:-$PROJECTS_ROOT/sandy-chaos}"
SITE_ROOT="${SITE_ROOT:-$PROJECTS_ROOT/ianmoog-site}"

SPINE_GIT_URL="${SPINE_GIT_URL:-}"
YGG_GIT_URL="${YGG_GIT_URL:-}"
TARA_GIT_URL="${TARA_GIT_URL:-}"
SANDY_CHAOS_GIT_URL="${SANDY_CHAOS_GIT_URL:-}"
IANMOOG_SITE_GIT_URL="${IANMOOG_SITE_GIT_URL:-}"

SPINE_GIT_REF="${SPINE_GIT_REF:-}"
YGG_GIT_REF="${YGG_GIT_REF:-}"
TARA_GIT_REF="${TARA_GIT_REF:-}"
SANDY_CHAOS_GIT_REF="${SANDY_CHAOS_GIT_REF:-}"
IANMOOG_SITE_GIT_REF="${IANMOOG_SITE_GIT_REF:-}"

ENABLE_SPINE="${ENABLE_SPINE:-1}"
ENABLE_YGG="${ENABLE_YGG:-1}"
ENABLE_TARA="${ENABLE_TARA:-1}"
ENABLE_SANDY_CHAOS="${ENABLE_SANDY_CHAOS:-1}"
ENABLE_IANMOOG_SITE="${ENABLE_IANMOOG_SITE:-0}"

PACMAN_PACKAGE_MANIFESTS="${PACMAN_PACKAGE_MANIFESTS:-state/profiles/arch-packages.base.txt}"
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
  local -a manifests=()
  local -a packages=()
  local manifest_line

  IFS=':' read -r -a manifests <<< "$PACMAN_PACKAGE_MANIFESTS"
  manifest_line="$(printf '%s ' "${manifests[@]}")"
  log "package manifests: $(trim "$manifest_line")"

  case "$mgr" in
    pacman)
      read_manifest_packages packages "${manifests[@]}"
      if [[ "${#packages[@]}" -eq 0 ]]; then
        packages=("${DEFAULT_PACMAN_PACKAGES[@]}")
      fi
      run_cmd sudo pacman -Syu --needed "${packages[@]}"
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

  export PATH="$prefix/bin:$PATH"
  run_cmd npm install -g openclaw
}

sync_repo_ref() {
  local dest="$1"
  local ref="$2"
  local label="$3"

  if [[ -z "$ref" || ! -d "$dest/.git" ]]; then
    return
  fi

  if [[ -n "$(git -C "$dest" status --porcelain 2>/dev/null)" ]]; then
    warn "$label has local changes; skipping ref checkout for $ref"
    return
  fi

  run_cmd git -C "$dest" fetch --all --tags --prune
  run_cmd git -C "$dest" checkout "$ref"
  if git -C "$dest" show-ref --verify --quiet "refs/remotes/origin/$ref"; then
    run_cmd git -C "$dest" pull --ff-only origin "$ref"
  fi
}

clone_or_pull() {
  local url="$1"
  local dest="$2"
  local label="$3"
  local ref="${4:-}"

  if [[ -d "$dest/.git" ]]; then
    if [[ -n "$url" && -z "$ref" ]]; then
      run_cmd git -C "$dest" pull --ff-only
    else
      log "use existing $label checkout: $dest"
    fi
    sync_repo_ref "$dest" "$ref" "$label"
    return
  fi

  if [[ -z "$url" ]]; then
    log "skip $label (no git URL provided)"
    return
  fi

  if [[ -e "$dest" ]]; then
    warn "$label target exists but is not a git checkout: $dest"
    return
  fi

  run_cmd git clone "$url" "$dest"
  sync_repo_ref "$dest" "$ref" "$label"
}

sync_component() {
  local enabled="$1"
  local url="$2"
  local dest="$3"
  local label="$4"
  local ref="${5:-}"

  if [[ "$enabled" != "1" ]]; then
    log "skip $label (disabled in profile)"
    return
  fi

  clone_or_pull "$url" "$dest" "$label" "$ref"
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

  WORKSPACE_ROOT="$WORKSPACE_ROOT" \
  YGG_ROOT="$YGG_ROOT" \
  TARA_ROOT="$TARA_ROOT" \
  PROJECTS_ROOT="$PROJECTS_ROOT" \
  SANDY_ROOT="$SANDY_ROOT" \
  SITE_ROOT="$SITE_ROOT" \
  SPINE_GIT_URL="$SPINE_GIT_URL" \
  YGG_GIT_URL="$YGG_GIT_URL" \
  TARA_GIT_URL="$TARA_GIT_URL" \
  SANDY_CHAOS_GIT_URL="$SANDY_CHAOS_GIT_URL" \
  IANMOOG_SITE_GIT_URL="$IANMOOG_SITE_GIT_URL" \
  SPINE_GIT_REF="$SPINE_GIT_REF" \
  YGG_GIT_REF="$YGG_GIT_REF" \
  TARA_GIT_REF="$TARA_GIT_REF" \
  SANDY_CHAOS_GIT_REF="$SANDY_CHAOS_GIT_REF" \
  IANMOOG_SITE_GIT_REF="$IANMOOG_SITE_GIT_REF" \
  ENABLE_SPINE="$ENABLE_SPINE" \
  ENABLE_YGG="$ENABLE_YGG" \
  ENABLE_TARA="$ENABLE_TARA" \
  ENABLE_SANDY_CHAOS="$ENABLE_SANDY_CHAOS" \
  ENABLE_IANMOOG_SITE="$ENABLE_IANMOOG_SITE" \
  python3 "$RENDER_PATH_CONTRACT_PY" \
    --registry "$COMPONENT_REGISTRY_PATH" \
    --profile "$PROFILE_NAME" \
    --contract-path "$PATH_CONTRACT_FILE" > "$PATH_CONTRACT_FILE"
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
  local ygg_cli_py="$YGG_ROOT/lib/ygg/cli.py"

  if [[ -x "$HOME/.local/bin/ygg" ]]; then
    run_cmd "$HOME/.local/bin/ygg" paths check --paths-file "$PATH_CONTRACT_FILE"
    return
  fi

  if [[ -f "$ygg_cli_py" ]]; then
    run_cmd python3 "$ygg_cli_py" paths check --paths-file "$PATH_CONTRACT_FILE"
    return
  fi

  warn "Unable to run ygg path checks (no ygg executable found)"
}

main() {
  log "== Ygg/OpenClaw Host Bootstrap =="
  log "profile:   $PROFILE_NAME"
  if [[ -n "$PROFILE_FILE" ]]; then
    log "profile file: $PROFILE_FILE"
  fi
  log "components registry: $COMPONENT_REGISTRY_PATH"
  log "workspace: $WORKSPACE_ROOT"
  log "ygg root:  $YGG_ROOT"
  log "tara root: $TARA_ROOT"
  log "projects:  $PROJECTS_ROOT"
  log "components: spine=$ENABLE_SPINE ygg=$ENABLE_YGG tara=$ENABLE_TARA sandy-chaos=$ENABLE_SANDY_CHAOS ianmoog-site=$ENABLE_IANMOOG_SITE"
  log

  run_cmd mkdir -p "$WORKSPACE_ROOT" "$YGG_ROOT" "$TARA_ROOT" "$PROJECTS_ROOT"

  if [[ "$SKIP_INSTALL" -ne 1 ]]; then
    local pkg_mgr
    pkg_mgr="$(detect_pkg_manager)"
    install_base_packages "$pkg_mgr"
  else
    log "skip package installation"
  fi

  ensure_openclaw_installed

  sync_component "$ENABLE_SPINE" "$SPINE_GIT_URL" "$WORKSPACE_ROOT" "spine workspace" "$SPINE_GIT_REF"
  sync_component "$ENABLE_YGG" "$YGG_GIT_URL" "$YGG_ROOT" "ygg" "$YGG_GIT_REF"
  sync_component "$ENABLE_TARA" "$TARA_GIT_URL" "$TARA_ROOT" "tara" "$TARA_GIT_REF"
  sync_component "$ENABLE_SANDY_CHAOS" "$SANDY_CHAOS_GIT_URL" "$SANDY_ROOT" "sandy-chaos" "$SANDY_CHAOS_GIT_REF"
  sync_component "$ENABLE_IANMOOG_SITE" "$IANMOOG_SITE_GIT_URL" "$SITE_ROOT" "ianmoog-site" "$IANMOOG_SITE_GIT_REF"

  write_path_contract
  wire_ygg_bin
  run_path_checks

  log
  log "Bootstrap complete."
  log "Next:"
  log "  1) Ensure PATH includes ~/.local/bin"
  log "  2) Run: ygg paths"
  log "  3) Run: ygg status"
  log "  4) Review profile assets under $YGG_ROOT/state/profiles"
}

main "$@"
