from __future__ import annotations

import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ygg.path_contract import RuntimePaths, resolve_runtime_paths

REPO_COMMAND_SURFACE: tuple[str, ...] = (
    "suggest",
    "work",
    "paths",
    "bootstrap",
    "inventory",
    "frontier",
    "raven",
    "graft",
    "beak",
    "root",
    "branch",
    "resume",
    "forge",
    "promote",
    "status",
    "mode",
    "run",
    "nyx",
    "checkpoint",
    "heimdall",
    "ratatoskr",
)

REPO_SYSTEM_SPECS: tuple[dict[str, Any], ...] = (
    {
        "id": "cli-control-plane",
        "title": "CLI control-plane",
        "ownershipClass": "ygg-canonical",
        "summary": "Canonical Ygg entrypoint, help/contracts surface, and operator-facing verb topology.",
        "files": ["lib/ygg/cli.py", "lib/ygg/frontier.py", "state/ygg/frontiers.json", "bin/ygg", "commands/README.md", "README.md"],
        "tests": ["tests/test_contracts.py"],
        "commands": ["suggest", "work", "root", "branch", "resume", "forge", "status", "frontier"],
    },
    {
        "id": "semantic-continuity-kernel",
        "title": "Semantic continuity kernel",
        "ownershipClass": "ygg-canonical",
        "summary": "Checkpoint/promote machinery plus structured programs/ideas registries under state/ygg/. These files are ygg-canonical: authoritative Ygg control-plane state.",
        "files": [
            "lib/ygg/continuity.py",
            "state/ygg/checkpoints",
            "state/ygg/programs.json",
            "state/ygg/ideas.json",
        ],
        "tests": ["tests/test_continuity.py"],
        "commands": ["checkpoint", "promote", "status"],
    },
    {
        "id": "runtime-embodiment-refresh",
        "title": "Runtime embodiment refresh",
        "ownershipClass": "ygg-canonical",
        "summary": "Heimdall runtime snapshot, fingerprinting, kernel event emission, and daily note handoff. Code is ygg-canonical; runtime outputs (state/runtime/ygg-self.json, event-queue.jsonl) are assistant-local machine state.",
        "files": ["lib/ygg/heimdall.py", "state/templates/ygg-self.example.json"],
        "tests": ["tests/test_heimdall.py"],
        "commands": ["heimdall"],
    },
    {
        "id": "event-routing-courier",
        "title": "Event routing courier",
        "ownershipClass": "bridge",
        "summary": "Ratatoskr event routing into daily notes and promotion-candidate sinks. This system is a bridge: it carries ygg-canonical events into assistant-local note surfaces without erasing provenance.",
        "files": ["lib/ygg/ratatoskr.py", "state/runtime/promotions.jsonl", "state/notes/promotions.md"],
        "tests": ["tests/test_ratatoskr.py"],
        "commands": ["ratatoskr"],
    },
    {
        "id": "bootstrap-and-path-contract",
        "title": "Bootstrap and path contract",
        "ownershipClass": "ygg-canonical",
        "summary": "Portable path resolution, registry/profile loading, and Arch-first bootstrap inspection.",
        "files": [
            "lib/ygg/path_contract.py",
            "lib/ygg/bootstrap_registry.py",
            "state/templates/ygg-paths.yaml.template",
            "state/profiles/components.yaml",
        ],
        "tests": [
            "tests/test_bootstrap_inspect.py",
            "tests/test_bootstrap_profiles.py",
            "tests/test_bootstrap_registry.py",
        ],
        "commands": ["paths", "bootstrap"],
    },
    {
        "id": "ravens-governed-roaming",
        "title": "RAVENS governed roaming cognition",
        "ownershipClass": "ygg-canonical",
        "summary": "Inspectable flights, return packets, and graft/beak proposal artifacts. Flight outputs are ygg-derived: reproducible from the canonical flight records.",
        "files": ["lib/ygg/ravens_v1.py", "docs/RAVENS.md", "docs/RAVENS-V1.md"],
        "tests": ["tests/test_ravens.py"],
        "commands": ["raven", "graft", "beak"],
    },
    {
        "id": "state-boundary-and-backups",
        "title": "State boundary and backups",
        "ownershipClass": "ygg-canonical",
        "summary": "Commit-safe templates/policy plus local backup/restore scripts for runtime surfaces. See docs/BRIDGE-OWNERSHIP-CONTRACT.md for the full ownership class model.",
        "files": [
            "state/README.md",
            "state/policy/STATE-BOUNDARY.md",
            "state/scripts/spine-backup.sh",
            "state/scripts/spine-restore.sh",
        ],
        "tests": [],
        "commands": ["bootstrap", "paths"],
    },
)

REPO_SPECULATIVE_TRACKS: tuple[dict[str, Any], ...] = (
    {
        "id": "response-cards-and-qa-layer",
        "title": "Response cards / per-command Q&A layer",
        "summary": "Roadmap-visible UX layer for suggested next commands and context-sensitive Q&A.",
        "docEvidence": ["docs/ROADMAP.md"],
        "missingFiles": [],
    },
    {
        "id": "topology-visualization-2d",
        "title": "2D branch topology visualization",
        "summary": "Inspectable topology view over lanes/branches once semantics are stable.",
        "docEvidence": ["docs/ROADMAP.md", "docs/NORTH-STAR.md"],
        "missingFiles": ["lib/ygg/topology.py"],
    },
    {
        "id": "voice-surface",
        "title": "Voice-first / voice-to-voice operational surface",
        "summary": "Conversational interface expansion over the same inspectable spine.",
        "docEvidence": ["docs/ROADMAP.md", "docs/NORTH-STAR.md"],
        "missingFiles": ["lib/ygg/voice.py"],
    },
    {
        "id": "ar-vr-branch-visualization",
        "title": "AR/VR branch visualization",
        "summary": "Experimental visualization layer explicitly deferred until 2D semantics are stable.",
        "docEvidence": ["docs/ROADMAP.md", "docs/NORTH-STAR.md"],
        "missingFiles": ["lib/ygg/immersive.py"],
    },
)

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


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        payload = json.loads(raw)
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _present_relatives(root: Path, relatives: list[str]) -> list[str]:
    present: list[str] = []
    for relative in relatives:
        if (root / relative).exists():
            present.append(relative)
    return present


def _system_status(*, files_present: list[str], tests_present: list[str], files_total: int, tests_total: int) -> str:
    if files_total == 0:
        return "missing"
    if len(files_present) == files_total and (tests_total == 0 or len(tests_present) == tests_total):
        return "implemented"
    if files_present or tests_present:
        return "partial"
    return "missing"


def _bridge_rows(root: Path) -> list[dict[str, Any]]:
    links_dir = root / "links"
    if not links_dir.exists():
        return []

    rows: list[dict[str, Any]] = []
    for path in sorted(links_dir.iterdir(), key=lambda item: item.name):
        if path.name == "README.md":
            continue
        row = _path_row(path, root, reason="Explicit bridge into assistant-home / spine-owned surface. Ownership class: bridge.")
        row["ownershipClass"] = "bridge"
        rows.append(row)
    return rows


def _state_surface_rows(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    # Each entry: (relative_path, reason, ownershipClass)
    # See docs/BRIDGE-OWNERSHIP-CONTRACT.md for class definitions.
    candidates = (
        ("state/ygg/programs.json", "Program registry seed for semantic continuity.", "ygg-canonical"),
        ("state/ygg/ideas.json", "Idea registry seed for incubation and promotion.", "ygg-canonical"),
        ("state/ygg/checkpoints", "Checkpoint ledger for semantic continuity decisions.", "ygg-canonical"),
        ("state/runtime/persona-mode.json", "Persisted persona override runtime state.", "assistant-local"),
        ("state/runtime/promotions.jsonl", "Promotion/event log for branch outcomes.", "ygg-derived"),
        ("state/runtime/ygg-self.json", "Live runtime embodiment snapshot emitted by Heimdall; machine-specific, not portable repo truth.", "assistant-local"),
        ("state/runtime/ygg-kernel.json", "Kernel boot/runtime state surface; machine-specific.", "assistant-local"),
        ("state/runtime/event-queue.jsonl", "Append-only event queue derived from runtime observations.", "ygg-derived"),
        ("state/runtime/promotion-candidates.jsonl", "Promotion candidates queued for review; derived from branch outcomes.", "ygg-derived"),
    )
    for relative, reason, ownership_class in candidates:
        path = root / relative
        if path.exists():
            row = _path_row(path, root, reason=reason)
            row["ownershipClass"] = ownership_class
            rows.append(row)
    return rows


def _repo_system_rows(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in REPO_SYSTEM_SPECS:
        files = list(spec.get("files") or [])
        tests = list(spec.get("tests") or [])
        files_present = _present_relatives(root, files)
        tests_present = _present_relatives(root, tests)
        status = _system_status(
            files_present=files_present,
            tests_present=tests_present,
            files_total=len(files),
            tests_total=len(tests),
        )
        if status == "missing":
            continue
        rows.append(
            {
                "id": spec["id"],
                "title": spec["title"],
                "ownershipClass": spec.get("ownershipClass", "ygg-canonical"),
                "status": status,
                "summary": spec["summary"],
                "commands": list(spec.get("commands") or []),
                "evidence": {
                    "filesPresent": files_present,
                    "filesExpected": files,
                    "testsPresent": tests_present,
                    "testsExpected": tests,
                },
            }
        )
    status_order = {"implemented": 0, "partial": 1, "missing": 2}
    rows.sort(key=lambda row: (status_order.get(str(row.get("status")), 9), str(row.get("title", ""))))
    return rows


def _speculative_rows(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in REPO_SPECULATIVE_TRACKS:
        docs_present = _present_relatives(root, list(spec.get("docEvidence") or []))
        if not docs_present:
            continue
        missing_files = [relative for relative in spec.get("missingFiles") or [] if not (root / relative).exists()]
        if spec.get("missingFiles") and not missing_files:
            continue
        rows.append(
            {
                "id": spec["id"],
                "title": spec["title"],
                "status": "speculative",
                "summary": spec["summary"],
                "evidence": {
                    "docsPresent": docs_present,
                    "missingFiles": missing_files,
                },
            }
        )
    return rows


def _next_target_rows(root: Path, systems: list[dict[str, Any]], bridges: list[dict[str, Any]], state_surfaces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    state_paths = {row["relativePath"] for row in state_surfaces}
    system_ids = {row["id"] for row in systems}

    if {"state/ygg/programs.json", "state/ygg/ideas.json"}.issubset(state_paths):
        rows.append(
            {
                "id": "semantic-registry-ops",
                "title": "Make programs/ideas first-class operational surfaces",
                "why": "The repo already has seeded semantic registries, but they are not yet exposed as dedicated query/edit commands.",
                "priority": "high",
            }
        )

    if bridges:
        rows.append(
            {
                "id": "bridge-ownership-tightening",
                "title": "Tighten Ygg vs spine ownership boundaries",
                "why": "Visible links back into assistant-home prove the bridge is real; next leverage is reducing ambiguity, not adding more surface area.",
                "priority": "high",
            }
        )

    if "runtime-embodiment-refresh" in system_ids and "event-routing-courier" in system_ids:
        rows.append(
            {
                "id": "topology-over-events",
                "title": "Build topology/inventory views over existing runtime and promotion events",
                "why": "Heimdall and Ratatoskr already emit structured state; the next gain is a queryable map rather than more note files.",
                "priority": "medium",
            }
        )

    return rows[:3]


def build_repo_inventory(root: str | Path) -> dict[str, Any]:
    root_path = Path(root).expanduser().resolve()
    systems = _repo_system_rows(root_path)
    bridges = _bridge_rows(root_path)
    state_surfaces = _state_surface_rows(root_path)
    speculative = _speculative_rows(root_path)
    ideas_payload = _load_json(root_path / "state" / "ygg" / "ideas.json") or {}
    programs_payload = _load_json(root_path / "state" / "ygg" / "programs.json") or {}

    summary = {
        "implementedCount": sum(1 for row in systems if row.get("status") == "implemented"),
        "partialCount": sum(1 for row in systems if row.get("status") == "partial"),
        "speculativeCount": len(speculative),
        "bridgeCount": len(bridges),
        "ideaCount": len(ideas_payload.get("ideas") or []),
        "programCount": len(programs_payload.get("programs") or []),
        "commandCount": len(REPO_COMMAND_SURFACE),
        "testCount": len(list((root_path / "tests").glob("test_*.py"))) if (root_path / "tests").exists() else 0,
    }

    ownership_contract = root_path / "docs" / "BRIDGE-OWNERSHIP-CONTRACT.md"
    return {
        "schema": "ygg-repo-inventory/v1",
        "generatedAt": datetime.now(UTC).isoformat(),
        "root": str(root_path),
        "ownershipContract": str(ownership_contract) if ownership_contract.exists() else None,
        "summary": summary,
        "commandSurface": list(REPO_COMMAND_SURFACE),
        "systems": systems,
        "bridges": bridges,
        "stateSurfaces": state_surfaces,
        "speculativeTracks": speculative,
        "nextTargets": _next_target_rows(root_path, systems, bridges, state_surfaces),
    }
