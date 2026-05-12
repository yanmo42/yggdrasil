from __future__ import annotations

import os
import pwd
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]

    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none"}:
        return None

    try:
        return int(value)
    except ValueError:
        return value


def parse_simple_yaml(path: Path) -> dict[str, Any]:
    """Parse a very small YAML subset: nested mappings with scalar values.

    This is intentionally minimal to avoid adding external YAML dependencies.
    It supports the shape used by config/ygg-paths.yaml.
    """

    text = path.read_text(encoding="utf-8")
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]

    for lineno, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue

        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.lstrip()
        if "#" in line:
            line = line.split("#", 1)[0].rstrip()
        if not line:
            continue
        if ":" not in line:
            raise ValueError(f"Unsupported YAML content at {path}:{lineno}: {raw}")

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise ValueError(f"Invalid indentation at {path}:{lineno}")

        parent = stack[-1][1]
        if not value:
            node: dict[str, Any] = {}
            parent[key] = node
            stack.append((indent, node))
        else:
            parent[key] = _parse_scalar(value)

    return root


def get_nested(data: dict[str, Any], dotted: str, default: Any = None) -> Any:
    cursor: Any = data
    for part in dotted.split("."):
        if not isinstance(cursor, dict) or part not in cursor:
            return default
        cursor = cursor[part]
    return cursor


def _coerce_path(value: Any, fallback: Path, *, base_dir: Path | None = None) -> Path:
    if value is None or value == "":
        return fallback

    path = Path(str(value)).expanduser()
    if not path.is_absolute() and base_dir is not None:
        path = (base_dir / path).resolve()
    else:
        path = path.resolve()
    return path


def _unique(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        out.append(path)
    return out


def _account_home() -> Path:
    """Return the OS account home, ignoring runtime HOME overrides when present."""
    try:
        return Path(pwd.getpwuid(os.getuid()).pw_dir)
    except Exception:  # pragma: no cover - defensive platform fallback
        return Path.home()


def candidate_contract_paths() -> list[Path]:
    home = Path.home()
    account_home = _account_home()
    module_root = Path(__file__).resolve().parents[1]  # usually ~/ygg/lib
    repo_root = module_root.parent if module_root.name == "lib" else module_root

    paths: list[Path] = []

    env_override = os.environ.get("YGG_PATHS_FILE")
    if env_override:
        paths.append(Path(env_override).expanduser())

    openclaw_workspace = os.environ.get("OPENCLAW_WORKSPACE")
    if openclaw_workspace:
        paths.append(Path(openclaw_workspace).expanduser() / "config" / "ygg-paths.yaml")

    paths.extend(
        [
            Path.cwd() / "config" / "ygg-paths.yaml",
            repo_root / "config" / "ygg-paths.yaml",
            home / ".openclaw" / "workspace-claw-main" / "config" / "ygg-paths.yaml",
            home / ".openclaw" / "workspace" / "config" / "ygg-paths.yaml",
            account_home / ".openclaw" / "workspace-claw-main" / "config" / "ygg-paths.yaml",
            account_home / ".openclaw" / "workspace" / "config" / "ygg-paths.yaml",
        ]
    )
    return _unique(paths)


@dataclass(frozen=True)
class RuntimePaths:
    contract_path: Path | None
    contract: dict[str, Any]
    parse_error: str | None
    spine_root: Path
    control_plane_root: Path
    control_plane_bin: Path
    work_repos_root: Path


def load_contract(path_override: str | Path | None = None) -> tuple[dict[str, Any], Path | None]:
    if path_override:
        contract_path = Path(path_override).expanduser().resolve()
        if not contract_path.exists():
            raise FileNotFoundError(f"Path contract not found: {contract_path}")
        return parse_simple_yaml(contract_path), contract_path

    for candidate in candidate_contract_paths():
        resolved = candidate.expanduser().resolve()
        if resolved.exists():
            return parse_simple_yaml(resolved), resolved

    return {}, None


def resolve_runtime_paths(path_override: str | Path | None = None) -> RuntimePaths:
    home = _account_home()
    fallback_spine = home / ".openclaw" / "workspace-claw-main"
    fallback_control_plane = home / "ygg"
    fallback_control_bin = home / ".local" / "bin" / "ygg"
    fallback_work_repos = home / "projects"

    contract: dict[str, Any] = {}
    contract_path: Path | None = None
    parse_error: str | None = None

    try:
        contract, contract_path = load_contract(path_override)
    except Exception as exc:  # pragma: no cover - fallback guard
        parse_error = str(exc)

    base_dir = contract_path.parent if contract_path else None

    return RuntimePaths(
        contract_path=contract_path,
        contract=contract,
        parse_error=parse_error,
        spine_root=_coerce_path(get_nested(contract, "paths.spine.root"), fallback_spine, base_dir=base_dir),
        control_plane_root=_coerce_path(
            get_nested(contract, "paths.control_plane.root"),
            fallback_control_plane,
            base_dir=base_dir,
        ),
        control_plane_bin=_coerce_path(
            get_nested(contract, "paths.control_plane.bin"),
            fallback_control_bin,
            base_dir=base_dir,
        ),
        work_repos_root=_coerce_path(
            get_nested(contract, "paths.work_repos.root"),
            fallback_work_repos,
            base_dir=base_dir,
        ),
    )


def _label(path: Path | None) -> str:
    return str(path) if path is not None else "(not found)"


def validate_runtime_paths(runtime: RuntimePaths) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    if runtime.parse_error:
        errors.append(f"failed to parse path contract: {runtime.parse_error}")

    if runtime.contract_path is None:
        errors.append(
            "no ygg path contract file found (set YGG_PATHS_FILE or create config/ygg-paths.yaml in the canonical workspace)"
        )
    else:
        if not runtime.contract_path.exists():
            errors.append(f"contract path is missing: {runtime.contract_path}")

    required_dirs = {
        "paths.spine.root": runtime.spine_root,
        "paths.control_plane.root": runtime.control_plane_root,
        "paths.work_repos.root": runtime.work_repos_root,
    }
    for key, directory in required_dirs.items():
        if not directory.exists():
            errors.append(f"{key} is missing: {directory}")
        elif not directory.is_dir():
            errors.append(f"{key} is not a directory: {directory}")

    expected_scripts = [
        runtime.spine_root / "scripts" / "work.py",
        runtime.spine_root / "scripts" / "resume.py",
    ]
    for script in expected_scripts:
        if not script.exists():
            errors.append(f"required script is missing: {script}")

    if not runtime.control_plane_bin.exists():
        warnings.append(f"control-plane bin not found: {runtime.control_plane_bin}")

    canonical_registry = get_nested(runtime.contract, "contracts.canonical_path_registry")
    if canonical_registry and runtime.contract_path is not None:
        canonical_path = _coerce_path(canonical_registry, runtime.contract_path, base_dir=runtime.contract_path.parent)
        if canonical_path != runtime.contract_path:
            warnings.append(
                "contracts.canonical_path_registry does not match loaded contract path: "
                f"{canonical_path} != {_label(runtime.contract_path)}"
            )
    elif runtime.contract_path is not None:
        warnings.append("contracts.canonical_path_registry is not set")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def runtime_payload(runtime: RuntimePaths) -> dict[str, Any]:
    return {
        "contract": {
            "path": _label(runtime.contract_path),
            "loaded": runtime.contract_path is not None and runtime.parse_error is None,
            "parse_error": runtime.parse_error,
            "candidates": [str(p) for p in candidate_contract_paths()],
        },
        "resolved": {
            "spine_root": str(runtime.spine_root),
            "control_plane_root": str(runtime.control_plane_root),
            "control_plane_bin": str(runtime.control_plane_bin),
            "work_repos_root": str(runtime.work_repos_root),
        },
    }
