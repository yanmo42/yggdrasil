from __future__ import annotations

import os
import re
import shlex
from datetime import datetime
from pathlib import Path
from typing import Any

from ygg.path_contract import parse_simple_yaml


def _variable_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    variables = registry.get("variables")
    if not isinstance(variables, dict):
        return {}
    return {str(key): value for key, value in variables.items() if isinstance(value, dict)}


def _component_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    components = registry.get("components")
    if not isinstance(components, dict):
        return {}
    return {str(key): value for key, value in components.items() if isinstance(value, dict)}


def _profile_map(component: dict[str, Any], profile: str) -> dict[str, Any]:
    profiles = component.get("profiles")
    if not isinstance(profiles, dict):
        return {}
    selected = profiles.get(profile)
    if not isinstance(selected, dict):
        return {}
    return selected


def _env_value(name: str | None, env: dict[str, str]) -> str | None:
    if not name:
        return None
    value = env.get(name)
    if value is None or value == "":
        return None
    return value


def _expand_placeholders(text: str, env: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return env.get(key, "")

    return re.sub(r"\$\{([^}]+)\}", replace, text)


def _bool_to_shell(value: Any) -> str:
    if isinstance(value, bool):
        return "1" if value else "0"
    lowered = str(value).strip().lower()
    if lowered in {"1", "true", "yes", "on"}:
        return "1"
    return "0"


def _resolve_root(raw: Any) -> str:
    text = str(raw or "").strip()
    if not text:
        return ""
    return str(Path(text).expanduser())


def _resolve_value(raw: Any, env: dict[str, str], *, root_like: bool = False) -> str:
    text = _expand_placeholders(str(raw or "").strip(), env)
    if root_like:
        return _resolve_root(text)
    return text


def _resolve_field(component: dict[str, Any], profile: str, field: str, env: dict[str, str]) -> str:
    env_name = str(component.get(f"env_{field}", "")).strip() or None
    env_override = _env_value(env_name, env)
    if env_override is not None:
        value: Any = env_override
    else:
        profile_block = _profile_map(component, profile)
        if field in profile_block:
            value = profile_block[field]
        else:
            value = component.get(f"default_{field}", "")

    if field == "enabled":
        return _bool_to_shell(value)
    if field == "root":
        return _resolve_value(value, env, root_like=True)
    return _resolve_value(value, env)


def _resolve_variable(variable: dict[str, Any], env: dict[str, str]) -> tuple[str, str]:
    env_name = str(variable.get("env", "")).strip()
    if not env_name:
        raise ValueError("Registry variable is missing `env`.")
    env_override = _env_value(env_name, env)
    if env_override is not None:
        return env_name, env_override
    default = variable.get("default", "")
    return env_name, _resolve_value(default, env, root_like=True)


def load_registry(path: str | Path) -> dict[str, Any]:
    registry_path = Path(path).expanduser().resolve()
    return parse_simple_yaml(registry_path)


def parse_profile_env(path: str | Path) -> dict[str, str]:
    profile_path = Path(path).expanduser().resolve()
    out: dict[str, str] = {}
    for raw in profile_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        out[key] = value
    return out


def read_package_manifest(path: str | Path) -> list[str]:
    manifest_path = Path(path).expanduser().resolve()
    packages: list[str] = []
    seen: set[str] = set()
    for raw in manifest_path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line in seen:
            continue
        seen.add(line)
        packages.append(line)
    return packages


def resolve_registry_assignments(path: str | Path, *, profile: str, env: dict[str, str] | None = None) -> dict[str, str]:
    env_map = dict(os.environ if env is None else env)
    registry_path = Path(path).expanduser().resolve()
    registry = load_registry(registry_path)
    variables = _variable_map(registry)
    components = _component_map(registry)

    assignments: dict[str, str] = {
        "COMPONENT_REGISTRY_FILE": str(registry_path),
        "COMPONENT_REGISTRY_SCHEMA": str(registry.get("schema", "")),
        "COMPONENT_REGISTRY_PROFILE": profile,
    }

    for _variable_id, variable in variables.items():
        env_name, value = _resolve_variable(variable, {**env_map, **assignments})
        assignments[env_name] = value

    component_ids: list[str] = []
    for component_id, component in components.items():
        component_ids.append(component_id)
        merged_env = {**env_map, **assignments}
        for field in ("root", "url", "ref", "enabled"):
            env_name = str(component.get(f"env_{field}", "")).strip()
            if not env_name:
                continue
            assignments[env_name] = _resolve_field(component, profile, field, merged_env)

    assignments["COMPONENT_IDS"] = " ".join(component_ids)
    return assignments


def render_shell_assignments(path: str | Path, *, profile: str, env: dict[str, str] | None = None) -> str:
    assignments = resolve_registry_assignments(path, profile=profile, env=env)
    registry = load_registry(path)
    components = _component_map(registry)

    lines = [
        f"COMPONENT_REGISTRY_FILE={shlex.quote(assignments['COMPONENT_REGISTRY_FILE'])}",
        f"COMPONENT_REGISTRY_SCHEMA={shlex.quote(assignments['COMPONENT_REGISTRY_SCHEMA'])}",
        f"COMPONENT_REGISTRY_PROFILE={shlex.quote(assignments['COMPONENT_REGISTRY_PROFILE'])}",
    ]
    for component_id, component in components.items():
        for field in ("root", "url", "ref", "enabled"):
            env_name = str(component.get(f"env_{field}", "")).strip()
            if not env_name:
                continue
            lines.append(f"{env_name}={shlex.quote(assignments[env_name])}")

    lines.append(f"COMPONENT_IDS={shlex.quote(assignments['COMPONENT_IDS'])}")
    return "\n".join(lines) + "\n"


def _component_root(component_id: str, registry: dict[str, Any], assignments: dict[str, str]) -> str:
    component = _component_map(registry).get(component_id, {})
    env_name = str(component.get("env_root", "")).strip()
    return assignments.get(env_name, "")


def render_path_contract(
    path: str | Path,
    *,
    profile: str,
    contract_path: str | Path,
    env: dict[str, str] | None = None,
) -> str:
    registry = load_registry(path)
    assignments = resolve_registry_assignments(path, profile=profile, env=env)
    config = registry.get("path_contract")
    if not isinstance(config, dict):
        raise ValueError("Component registry is missing top-level `path_contract` config.")

    work_root_env = str(config.get("work_repos_root_env", "")).strip()
    work_repos_root = assignments.get(work_root_env, "")

    spine_cfg = config.get("spine")
    control_cfg = config.get("control_plane")
    work_cfg = config.get("work_repos")
    if not isinstance(spine_cfg, dict) or not isinstance(control_cfg, dict) or not isinstance(work_cfg, dict):
        raise ValueError("Registry path_contract config is incomplete.")

    spine_root = _component_root(str(spine_cfg.get("component", "")), registry, assignments)
    control_root = _component_root(str(control_cfg.get("component", "")), registry, assignments)

    def fmt(template: Any, root: str) -> str:
        return str(template or "").format(root=root)

    contract_path_str = str(Path(contract_path).expanduser())
    lines = [
        "schema: ygg-paths/v1",
        f"profile: {profile}",
        f"updated_on: {datetime.now().date().isoformat()}",
        "",
        "paths:",
        "  spine:",
        f"    root: {spine_root}",
        f"    config_dir: {fmt(spine_cfg.get('config_dir', '{root}/config'), spine_root)}",
        f"    memory_dir: {fmt(spine_cfg.get('memory_dir', '{root}/memory'), spine_root)}",
        f"    backups_dir: {fmt(spine_cfg.get('backups_dir', '{root}/backups'), spine_root)}",
        "",
        "  control_plane:",
        f"    name: {control_cfg.get('name', 'ygg')}",
        f"    root: {control_root}",
        f"    bin: {fmt(control_cfg.get('bin', '{root}/bin/ygg'), control_root)}",
        "",
        "  work_repos:",
        f"    root: {work_repos_root}",
    ]

    work_components = work_cfg.get("components")
    if not isinstance(work_components, dict):
        raise ValueError("Registry path_contract.work_repos.components must be a mapping.")
    for key, component_id in work_components.items():
        root = _component_root(str(component_id), registry, assignments)
        lines.append(f"    {key}: {root}")

    lines.extend(
        [
            "",
            "contracts:",
            f"  canonical_state_owner: {config.get('canonical_state_owner', 'spine')}",
            f"  canonical_path_registry: {contract_path_str}",
            f"  branch_backflow: {shlex.quote(str(config.get('branch_backflow', 'Durable outcomes from repos should be promoted back into spine memory/state.')))}",
        ]
    )
    return "\n".join(lines) + "\n"
