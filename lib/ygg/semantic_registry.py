from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

REGISTRY_FILES = {
    "program": "state/ygg/programs.json",
    "idea": "state/ygg/ideas.json",
}

REGISTRY_COLLECTIONS = {
    "program": "programs",
    "idea": "ideas",
}

STATUS_VOCAB = {
    "program": {"active", "watching", "blocked", "hibernating", "completed", "dropped"},
    "idea": {"incubating", "testing", "parked", "adopted", "rejected"},
}

CLAIM_TIERS = {"defensible", "plausible", "speculative"}

REQUIRED_CREATE_FIELDS = {
    "program": {"id", "title", "status"},
    "idea": {"id", "title", "status"},
}

LIST_FIELDS = {
    "program": {"relatedLanes", "artifacts", "notes"},
    "idea": {"tags", "notes"},
}

IDEA_LINK_FIELDS = {
    "programs": "links.programs",
    "checkpoints": "links.checkpoints",
    "promotionTargets": "links.promotionTargets",
}


class SemanticRegistryValidationError(ValueError):
    pass


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _copy_json(value: Any) -> Any:
    return json.loads(json.dumps(value))


def _require_mapping(value: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SemanticRegistryValidationError(f"{label} must be a JSON object.")
    return value


def _normalize_id(item_id: Any, *, label: str = "id") -> str:
    value = str(item_id or "").strip()
    if not value:
        raise SemanticRegistryValidationError(f"{label} is required.")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-")
    if value.startswith("-") or value.endswith("-") or "--" in value or any(ch not in allowed for ch in value):
        raise SemanticRegistryValidationError(
            f"{label} must use lowercase letters, numbers, and single hyphens only."
        )
    return value


def _require_nonempty_string(value: Any, *, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise SemanticRegistryValidationError(f"{label} is required.")
    return text


def _validate_string_list(value: Any, *, label: str) -> list[str]:
    if not isinstance(value, list):
        raise SemanticRegistryValidationError(f"{label} must be a list.")
    normalized: list[str] = []
    for entry in value:
        text = str(entry or "").strip()
        if not text:
            raise SemanticRegistryValidationError(f"{label} entries must be non-empty strings.")
        normalized.append(text)
    return normalized


def _normalize_idea_links(value: Any) -> dict[str, list[str]]:
    links = _require_mapping(value, label="links")
    normalized: dict[str, list[str]] = {}
    for key in IDEA_LINK_FIELDS:
        if key in links:
            values = _validate_string_list(links[key], label=IDEA_LINK_FIELDS[key])
            if key == "programs":
                values = [_normalize_id(entry, label=IDEA_LINK_FIELDS[key]) for entry in values]
            normalized[key] = values
    return normalized


def _validate_registry_item(kind: str, item: Any) -> dict[str, Any]:
    row = _require_mapping(item, label=f"{kind} item")
    normalized = _copy_json(row)
    normalized["id"] = _normalize_id(normalized.get("id"))
    normalized["title"] = _require_nonempty_string(normalized.get("title"), label="title")
    status = normalized.get("status")
    if status is not None:
        normalized["status"] = _require_nonempty_string(status, label="status")
        if normalized["status"] not in STATUS_VOCAB[kind]:
            raise SemanticRegistryValidationError(
                f"status must be one of: {', '.join(sorted(STATUS_VOCAB[kind]))}."
            )
    for field in LIST_FIELDS[kind]:
        if field in normalized:
            normalized[field] = _validate_string_list(normalized[field], label=field)
    if kind == "idea":
        if "claimTier" in normalized:
            normalized["claimTier"] = _require_nonempty_string(normalized["claimTier"], label="claimTier")
            if normalized["claimTier"] not in CLAIM_TIERS:
                raise SemanticRegistryValidationError(
                    f"claimTier must be one of: {', '.join(sorted(CLAIM_TIERS))}."
                )
        if "links" in normalized:
            normalized["links"] = _normalize_idea_links(normalized["links"])
    return normalized


def _validate_registry_payload(kind: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    collection_key = REGISTRY_COLLECTIONS[kind]
    rows = payload.get(collection_key)
    if not isinstance(rows, list):
        raise ValueError(f"Semantic registry `{payload['path']}` is missing list field `{collection_key}`.")
    validated: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        item = _validate_registry_item(kind, row)
        item_id = item["id"]
        if item_id in seen:
            raise SemanticRegistryValidationError(f"Duplicate {kind} id `{item_id}`.")
        seen.add(item_id)
        validated.append(item)
    return validated


def _write_registry(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _registry_path(root: str | Path, kind: str) -> Path:
    try:
        relative = REGISTRY_FILES[kind]
    except KeyError as exc:
        raise ValueError(f"Unknown semantic registry kind: {kind}") from exc
    return Path(root).expanduser().resolve() / relative


def load_registry(root: str | Path, kind: str) -> dict[str, Any]:
    path = _registry_path(root, kind)
    if not path.exists():
        raise FileNotFoundError(f"Semantic registry does not exist: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["path"] = path
    rows = _validate_registry_payload(kind, payload)
    return {
        "kind": kind,
        "path": path,
        "version": payload.get("version"),
        "updatedAt": payload.get("updatedAt"),
        "items": rows,
    }


def list_registry_items(root: str | Path, kind: str) -> dict[str, Any]:
    payload = load_registry(root, kind)
    return payload


def get_registry_item(root: str | Path, kind: str, item_id: str) -> dict[str, Any]:
    payload = load_registry(root, kind)
    for row in payload["items"]:
        if row.get("id") == item_id:
            return row
    raise KeyError(f"No {kind} with id `{item_id}`.")


def create_registry_item(root: str | Path, kind: str, item: dict[str, Any], *, now: str | None = None) -> dict[str, Any]:
    payload = load_registry(root, kind)
    normalized = _require_mapping(_copy_json(item), label=f"{kind} item")
    missing = sorted(field for field in REQUIRED_CREATE_FIELDS[kind] if not str(normalized.get(field) or "").strip())
    if missing:
        raise SemanticRegistryValidationError(f"Missing required fields: {', '.join(missing)}.")
    candidate = _validate_registry_item(kind, normalized)
    if any(existing.get("id") == candidate["id"] for existing in payload["items"]):
        raise SemanticRegistryValidationError(f"{kind} id `{candidate['id']}` already exists.")
    rows = [_copy_json(existing) for existing in payload["items"]]
    rows.append(candidate)
    updated_at = now or _now_iso()
    file_payload = {
        "version": payload.get("version"),
        "updatedAt": updated_at,
        REGISTRY_COLLECTIONS[kind]: rows,
    }
    _write_registry(payload["path"], file_payload)
    return {
        "kind": kind,
        "path": payload["path"],
        "updatedAt": updated_at,
        "item": candidate,
    }


def update_registry_item(
    root: str | Path, kind: str, item_id: str, patch: dict[str, Any], *, now: str | None = None
) -> dict[str, Any]:
    payload = load_registry(root, kind)
    target_id = _normalize_id(item_id)
    normalized_patch = _require_mapping(_copy_json(patch), label="patch")
    if "id" in normalized_patch and normalized_patch["id"] != target_id:
        raise SemanticRegistryValidationError("id cannot be changed.")
    normalized_patch.pop("id", None)
    rows = [_copy_json(existing) for existing in payload["items"]]
    for index, existing in enumerate(rows):
        if existing.get("id") != target_id:
            continue
        updated = _copy_json(existing)
        updated.update(normalized_patch)
        updated["id"] = target_id
        candidate = _validate_registry_item(kind, updated)
        rows[index] = candidate
        updated_at = now or _now_iso()
        file_payload = {
            "version": payload.get("version"),
            "updatedAt": updated_at,
            REGISTRY_COLLECTIONS[kind]: rows,
        }
        _write_registry(payload["path"], file_payload)
        return {
            "kind": kind,
            "path": payload["path"],
            "updatedAt": updated_at,
            "item": candidate,
        }
    raise KeyError(f"No {kind} with id `{target_id}`.")


def link_idea_registry_item(
    root: str | Path,
    item_id: str,
    *,
    programs: list[str] | None = None,
    checkpoints: list[str] | None = None,
    promotion_targets: list[str] | None = None,
    now: str | None = None,
) -> dict[str, Any]:
    patch: dict[str, Any] = {}
    updates = {
        "programs": programs,
        "checkpoints": checkpoints,
        "promotionTargets": promotion_targets,
    }
    if not any(value for value in updates.values()):
        raise SemanticRegistryValidationError(
            "At least one link target is required: --program, --checkpoint, or --promotion-target."
        )
    payload = get_registry_item(root, "idea", item_id)
    links = _copy_json(payload.get("links") or {})
    for key, values in updates.items():
        if values is None:
            continue
        combined = list(links.get(key) or [])
        for value in values:
            text = str(value or "").strip()
            if not text:
                raise SemanticRegistryValidationError(f"{IDEA_LINK_FIELDS[key]} entries must be non-empty strings.")
            if key == "programs":
                text = _normalize_id(text, label=IDEA_LINK_FIELDS[key])
            if text not in combined:
                combined.append(text)
        links[key] = combined
    patch["links"] = links
    return update_registry_item(root, "idea", item_id, patch, now=now)
