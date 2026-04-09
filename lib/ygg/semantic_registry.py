from __future__ import annotations

import json
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
    collection_key = REGISTRY_COLLECTIONS[kind]
    rows = payload.get(collection_key)
    if not isinstance(rows, list):
        raise ValueError(f"Semantic registry `{path}` is missing list field `{collection_key}`.")
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
