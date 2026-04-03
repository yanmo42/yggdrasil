from __future__ import annotations

import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ygg.path_contract import RuntimePaths, resolve_runtime_paths

DEFAULT_MAX_REPO_DEPTH = 3
DEFAULT_SCAN_EXCLUDES = {
    ".cache",
    ".local",
    ".npm",
    ".npm-global",
    ".vscode-server",
}

RUNTIME_RELATIVE_PATHS: tuple[tuple[str, str], ...] = (
    (".claude", "Local Claude runtime state and history; do not treat as portable source."),
    (".codex", "Local Codex runtime state and history; do not treat as portable source."),
    (".ollama", "Local model/runtime state; portable only as configuration, not as raw state."),
    (".openclaw/agents", "OpenClaw agent runtime state; keep out of git."),
    (".openclaw/browser", "OpenClaw browser/runtime payloads; keep out of git."),
    (".openclaw/memory", "OpenClaw live memory databases; back up, do not commit."),
    (".openclaw/tasks", "OpenClaw task runtime DB; back up, do not commit."),
)

DISPOSABLE_RELATIVE_PATHS: tuple[tuple[str, str], ...] = (
    (".cache", "General cache directory; disposable."),
    (".npm", "NPM package cache; reproducible."),
    (".npm-global", "Global npm install prefix; rebuild from manifest/bootstrap."),
    (".vscode-server", "Editor server/cache payloads; reproducible."),
    (".zcompdump", "Zsh completion cache; disposable."),
)

TEMPLATE_RELATIVE_PATHS: tuple[tuple[str, str], ...] = (
    (".zshrc", "Operator shell bootstrap; keep as template and strip secrets."),
    (".gitconfig", "Portable git preferences; template or selectively commit."),
    (".config/starship.toml", "Portable prompt configuration."),
    (".config/systemd/user", "Portable user-level automation units."),
)

SECRET_RELATIVE_PATHS: tuple[tuple[str, str], ...] = (
    (".zshrc", "Shell config may contain plaintext API tokens; move secrets to env/secret store before GitHub."),
    (".openclaw/openclaw.json", "OpenClaw machine config may contain provider/auth state."),
    (".codex/auth.json", "Codex auth state; never commit."),
    (".claude/.credentials.json", "Claude auth state; never commit."),
    (".config/gh/hosts.yml", "GitHub CLI auth state; never commit."),
    (".config/ygg/backup.key", "Backup key material; never commit."),
)


def _path_row(path: Path, root: Path, *, reason: str | None = None) -> dict[str, Any]:
    absolute = path.expanduser()
    if not absolute.is_absolute():
        absolute = (root / absolute).absolute()
    else:
        absolute = absolute.absolute()
    resolved = absolute.resolve()
    try:
        relative = absolute.relative_to(root.resolve())
        relative_text = "." if not relative.parts else str(relative)
    except ValueError:
        relative_text = str(absolute)

    row: dict[str, Any] = {
        "path": str(absolute),
        "relativePath": relative_text,
        "exists": absolute.exists(),
        "kind": _kind_for_path(absolute),
    }
    if resolved != absolute:
        row["resolvedPath"] = str(resolved)
    if reason:
        row["reason"] = reason
    return row


def _kind_for_path(path: Path) -> str:
    if path.is_symlink():
        return "symlink"
    if path.is_dir():
        return "dir"
    if path.is_file():
        return "file"
    return "missing"


def _append_unique(rows: list[dict[str, Any]], row: dict[str, Any]) -> None:
    key = row["path"]
    if any(existing["path"] == key for existing in rows):
        return
    rows.append(row)


def _descends_from(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def discover_git_repos(
    root: str | Path,
    *,
    max_depth: int = DEFAULT_MAX_REPO_DEPTH,
    scan_excludes: set[str] | None = None,
) -> list[Path]:
    root_path = Path(root).expanduser().resolve()
    excludes = scan_excludes or DEFAULT_SCAN_EXCLUDES
    repos: list[Path] = []

    for current_root, dirnames, _filenames in os.walk(root_path, topdown=True):
        current_path = Path(current_root)
        try:
            depth = len(current_path.relative_to(root_path).parts)
        except ValueError:
            depth = 0

        if depth == 0:
            dirnames[:] = [name for name in dirnames if name not in excludes]

        if ".git" in dirnames:
            repos.append(current_path)
            dirnames[:] = [name for name in dirnames if name != ".git"]

        if depth >= max_depth:
            dirnames[:] = []

    return sorted({repo.resolve() for repo in repos})


def summarize_git_repo(repo: Path) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "status", "--short", "--branch"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return summary

    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        return summary

    branch = lines[0]
    dirty_lines = lines[1:]
    summary["branch"] = branch
    summary["dirty"] = bool(dirty_lines)
    summary["modifiedCount"] = sum(1 for line in dirty_lines if not line.startswith("??"))
    summary["untrackedCount"] = sum(1 for line in dirty_lines if line.startswith("??"))
    if dirty_lines:
        summary["sampleChanges"] = dirty_lines[:5]
    return summary


def _contract_work_repos(runtime: RuntimePaths) -> list[tuple[str, Path]]:
    work_repos = runtime.contract.get("paths", {}).get("work_repos", {})
    if not isinstance(work_repos, dict):
        return []

    out: list[tuple[str, Path]] = []
    for key, value in work_repos.items():
        if key == "root" or value in (None, ""):
            continue
        out.append((str(key), Path(str(value)).expanduser().resolve()))
    return out


def build_inventory(
    root: str | Path,
    *,
    max_repo_depth: int = DEFAULT_MAX_REPO_DEPTH,
    path_override: str | Path | None = None,
) -> dict[str, Any]:
    root_path = Path(root).expanduser().resolve()
    runtime = resolve_runtime_paths(path_override)
    git_repos = discover_git_repos(root_path, max_depth=max_repo_depth)

    git_repo_rows: list[dict[str, Any]] = []
    for repo in git_repos:
        row = _path_row(repo, root_path)
        row["git"] = summarize_git_repo(repo)
        git_repo_rows.append(row)

    top_level = sorted(root_path.iterdir(), key=lambda item: item.name)
    top_level_rows = [_path_row(path, root_path) for path in top_level]

    classification: dict[str, list[dict[str, Any]]] = {
        "coreCandidates": [],
        "protocolContracts": [],
        "templateCandidates": [],
        "documentationSurfaces": [],
        "optionalProjects": [],
        "legacySurfaces": [],
        "runtimeState": [],
        "disposableCaches": [],
        "secretSurfaces": [],
    }

    for path, reason in (
        (runtime.control_plane_root, "Canonical operator-facing control plane from the Ygg path contract."),
        (runtime.spine_root, "Canonical spine/runtime owner from the Ygg path contract."),
    ):
        _append_unique(classification["coreCandidates"], _path_row(path, root_path, reason=reason))

    tara_repo = root_path / "tara"
    tara_repo_path = tara_repo.resolve() if tara_repo.exists() else None
    if tara_repo.exists():
        _append_unique(
            classification["protocolContracts"],
            _path_row(tara_repo, root_path, reason="Protocol/schema repo for cross-session and cross-arc handoff contracts."),
        )

    for key, repo_path in _contract_work_repos(runtime):
        if "site" in key:
            _append_unique(
                classification["documentationSurfaces"],
                _path_row(repo_path, root_path, reason=f"Contract-declared documentation/distribution surface: {key}."),
            )
        else:
            _append_unique(
                classification["optionalProjects"],
                _path_row(repo_path, root_path, reason=f"Contract-declared work repo: {key}."),
            )

    for repo in git_repos:
        if repo in {runtime.control_plane_root.resolve(), runtime.spine_root.resolve()}:
            continue
        if tara_repo_path is not None and repo == tara_repo_path:
            continue
        if _descends_from(repo, runtime.work_repos_root):
            if "site" in repo.name:
                _append_unique(
                    classification["documentationSurfaces"],
                    _path_row(repo, root_path, reason="Git repo under work-repos root that looks like a site/docs surface."),
                )
            else:
                _append_unique(
                    classification["optionalProjects"],
                    _path_row(repo, root_path, reason="Git repo under work-repos root; treat as optional module until promoted."),
                )
        elif "legacy" in repo.name or "legacy" in str(repo):
            _append_unique(
                classification["legacySurfaces"],
                _path_row(repo, root_path, reason="Legacy repo surface; inspect before promoting anything out of it."),
            )

    assistant_legacy = root_path / "projects" / "_assistant_home_legacy_20260307-203553"
    if assistant_legacy.exists():
        _append_unique(
            classification["legacySurfaces"],
            _path_row(assistant_legacy, root_path, reason="Archived assistant-home snapshot; reference only."),
        )

    for relative_path, reason in TEMPLATE_RELATIVE_PATHS:
        path = root_path / relative_path
        if path.exists():
            _append_unique(classification["templateCandidates"], _path_row(path, root_path, reason=reason))

    for relative_path, reason in RUNTIME_RELATIVE_PATHS:
        path = root_path / relative_path
        if path.exists():
            _append_unique(classification["runtimeState"], _path_row(path, root_path, reason=reason))

    for relative_path, reason in DISPOSABLE_RELATIVE_PATHS:
        path = root_path / relative_path
        if path.exists():
            _append_unique(classification["disposableCaches"], _path_row(path, root_path, reason=reason))

    for relative_path, reason in SECRET_RELATIVE_PATHS:
        path = root_path / relative_path
        if path.exists():
            _append_unique(classification["secretSurfaces"], _path_row(path, root_path, reason=reason))

    generated_at = datetime.now(UTC).isoformat()
    return {
        "schema": "ygg-host-inventory/v1",
        "generatedAt": generated_at,
        "root": str(root_path),
        "contract": {
            "path": str(runtime.contract_path) if runtime.contract_path else None,
            "parseError": runtime.parse_error,
            "spineRoot": str(runtime.spine_root),
            "controlPlaneRoot": str(runtime.control_plane_root),
            "workReposRoot": str(runtime.work_repos_root),
        },
        "topLevel": top_level_rows,
        "gitRepos": git_repo_rows,
        "classification": classification,
    }
