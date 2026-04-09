from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ContinuityRecord:
    id: str
    kind: str
    title: str
    summary: str
    text: str
    timestamp: str | None
    authority: str
    tags: tuple[str, ...]
    links: tuple[str, ...]
    source_path: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["tags"] = list(self.tags)
        payload["links"] = list(self.links)
        payload["sourcePath"] = payload.pop("source_path")
        return payload


TARGET_SURFACES = (
    "state/ygg/checkpoints",
    "state/ygg/ideas.json",
    "state/ygg/programs.json",
    "state/runtime/event-queue.jsonl",
    "state/runtime/promotions.jsonl",
)


def _compact(parts: list[str | None]) -> str:
    return "\n".join(part.strip() for part in parts if part and str(part).strip())


def _ensure_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _normalize_path(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def _program_link_ids(program_ids: list[Any]) -> list[str]:
    return [f"program:{str(item).strip()}" for item in program_ids if str(item).strip()]


def _checkpoint_link_ids(root: Path, checkpoint_paths: list[Any]) -> list[str]:
    links: list[str] = []
    for raw in checkpoint_paths:
        raw_str = str(raw).strip()
        if not raw_str:
            continue
        stem = Path(raw_str).stem
        if stem:
            links.append(f"checkpoint:{stem}")
            continue
        resolved = (root / raw_str).resolve()
        links.append(f"checkpoint:{resolved.stem}")
    return links


def load_continuity_corpus(root: str | Path) -> list[ContinuityRecord]:
    repo_root = Path(root).expanduser().resolve()
    records: list[ContinuityRecord] = []
    records.extend(_load_checkpoints(repo_root))
    records.extend(_load_registry(repo_root, "idea"))
    records.extend(_load_registry(repo_root, "program"))
    records.extend(_load_events(repo_root))
    records.extend(_load_promotions(repo_root))
    return sorted(records, key=lambda record: (record.timestamp or "", record.id))


def _load_checkpoints(root: Path) -> list[ContinuityRecord]:
    directory = root / "state" / "ygg" / "checkpoints"
    if not directory.exists():
        return []
    records: list[ContinuityRecord] = []
    for path in sorted(directory.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        lane = str(payload.get("lane") or "").strip()
        title = f"Checkpoint: {lane or path.stem}"
        tags = tuple(tag for tag in {"checkpoint", lane, str(payload.get("disposition") or "").strip().lower()} if tag)
        text = _compact(
            [
                title,
                payload.get("summary"),
                payload.get("evidence"),
                payload.get("next_action"),
                payload.get("promotion_target"),
                lane,
                payload.get("disposition"),
            ]
        )
        records.append(
            ContinuityRecord(
                id=f"checkpoint:{path.stem}",
                kind="checkpoint",
                title=title,
                summary=str(payload.get("summary") or ""),
                text=text,
                timestamp=str(payload.get("timestamp")) if payload.get("timestamp") else None,
                authority="checkpoint",
                tags=tuple(sorted(tags)),
                links=tuple(link for link in (f"lane:{lane}" if lane else "",) if link),
                source_path=_normalize_path(root, path),
                metadata={
                    "lane": lane,
                    "disposition": payload.get("disposition"),
                    "promotionTarget": payload.get("promotion_target"),
                    "evidence": payload.get("evidence"),
                    "nextAction": payload.get("next_action"),
                },
            )
        )
    return records


def _load_registry(root: Path, kind: str) -> list[ContinuityRecord]:
    path = root / "state" / "ygg" / f"{kind}s.json"
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    collection = payload.get(f"{kind}s")
    if not isinstance(collection, list):
        raise ValueError(f"Registry `{path}` is missing `{kind}s` list.")
    records: list[ContinuityRecord] = []
    for row in collection:
        row_id = str(row.get("id") or "").strip()
        title = str(row.get("title") or row_id or f"{kind}").strip()
        links_block = row.get("links") if isinstance(row.get("links"), dict) else {}
        related_lanes = _ensure_list(row.get("relatedLanes"))
        explicit_links = []
        explicit_links.extend(_checkpoint_link_ids(root, _ensure_list(links_block.get("checkpoints"))))
        explicit_links.extend(_program_link_ids(_ensure_list(links_block.get("programs"))))
        explicit_links.extend(f"lane:{str(item).strip()}" for item in related_lanes if str(item).strip())
        text = _compact(
            [
                title,
                row.get("summary"),
                row.get("nextAction"),
                row.get("owner"),
                row.get("origin"),
                row.get("priority"),
                row.get("status"),
                row.get("kind"),
                "\n".join(str(item) for item in related_lanes),
                "\n".join(str(item) for item in _ensure_list(row.get("artifacts"))),
                "\n".join(str(item) for item in _ensure_list((links_block or {}).get("promotionTargets"))),
            ]
        )
        tags = {
            str(tag).strip()
            for tag in _ensure_list(row.get("tags"))
            if str(tag).strip()
        }
        if kind == "idea":
            tags.add("idea")
        else:
            tags.add("program")
        authority = "idea" if kind == "idea" else "program"
        metadata = dict(row)
        metadata["registryUpdatedAt"] = payload.get("updatedAt")
        records.append(
            ContinuityRecord(
                id=f"{kind}:{row_id}",
                kind=kind,
                title=title,
                summary=str(row.get("summary") or ""),
                text=text,
                timestamp=str(payload.get("updatedAt")) if payload.get("updatedAt") else None,
                authority=authority,
                tags=tuple(sorted(tags)),
                links=tuple(sorted({link for link in explicit_links if link})),
                source_path=_normalize_path(root, path),
                metadata=metadata,
            )
        )
    return records


def _load_events(root: Path) -> list[ContinuityRecord]:
    path = root / "state" / "runtime" / "event-queue.jsonl"
    if not path.exists():
        return []
    records: list[ContinuityRecord] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            row = json.loads(raw_line)
            row_id = str(row.get("id") or f"line-{line_no}").strip()
            links = row.get("links") if isinstance(row.get("links"), dict) else {}
            explicit_links = []
            for key, prefix in (("laneId", "lane"), ("taskId", "task"), ("sessionKey", "session")):
                value = links.get(key)
                if value:
                    explicit_links.append(f"{prefix}:{value}")
            details = row.get("details") if isinstance(row.get("details"), dict) else {}
            text = _compact(
                [
                    row.get("kind"),
                    row.get("summary"),
                    row.get("source"),
                    row.get("importance"),
                    json.dumps(details, sort_keys=True, ensure_ascii=False),
                ]
            )
            records.append(
                ContinuityRecord(
                    id=f"event:{row_id}",
                    kind="event",
                    title=str(row.get("summary") or row.get("kind") or row_id),
                    summary=str(row.get("summary") or ""),
                    text=text,
                    timestamp=str(row.get("timestamp")) if row.get("timestamp") else None,
                    authority="runtime-event",
                    tags=tuple(sorted({str(row.get("kind") or ""), str(row.get("source") or ""), str(row.get("importance") or "")} - {""})),
                    links=tuple(sorted(explicit_links)),
                    source_path=_normalize_path(root, path),
                    metadata={"line": line_no, **row},
                )
            )
    return records


def _load_promotions(root: Path) -> list[ContinuityRecord]:
    path = root / "state" / "runtime" / "promotions.jsonl"
    if not path.exists():
        return []
    records: list[ContinuityRecord] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            row = json.loads(raw_line)
            domain = str(row.get("domain") or "").strip()
            task = str(row.get("task") or "").strip()
            title = f"Promotion: {domain}/{task}".strip("/")
            explicit_links = []
            if domain:
                explicit_links.append(f"domain:{domain}")
            if task:
                explicit_links.append(f"task:{task}")
                explicit_links.append(f"lane:{task}")
            artifacts = [str(item).strip() for item in _ensure_list(row.get("artifacts")) if str(item).strip()]
            tags = {"promotion", str(row.get("disposition") or "").strip(), domain, task}
            text = _compact(
                [
                    title,
                    row.get("note"),
                    row.get("disposition"),
                    domain,
                    task,
                    "\n".join(artifacts),
                ]
            )
            identifier = f"{row.get('timestamp')}-{domain}-{task}-{line_no}".strip("-")
            records.append(
                ContinuityRecord(
                    id=f"promotion:{identifier}",
                    kind="promotion",
                    title=title,
                    summary=str(row.get("note") or ""),
                    text=text,
                    timestamp=str(row.get("timestamp")) if row.get("timestamp") else None,
                    authority="promotion-log",
                    tags=tuple(sorted(tag for tag in tags if tag)),
                    links=tuple(sorted(explicit_links)),
                    source_path=_normalize_path(root, path),
                    metadata={"line": line_no, **row},
                )
            )
    return records
