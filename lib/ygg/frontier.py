from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_SC_RELATIVE_ROOT = Path.home() / "projects" / "sandy-chaos"
DEFAULT_YGG_ROOT = Path(__file__).resolve().parents[2]
FRONTIER_REGISTRY_RELATIVE_PATH = Path("state/ygg/frontiers.json")
FRONTIER_QUEUE_RELATIVE_PATH = Path("state/ygg/frontier-queue.json")
DEFAULT_ASSISTANT_WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", Path.home() / ".openclaw" / "workspace-claw-main")).expanduser()


@dataclass(frozen=True)
class AuditSource:
    path: str
    kind: str
    authority: str
    used_for: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "kind": self.kind,
            "authority": self.authority,
            "usedFor": list(self.used_for),
        }


def resolve_sc_root(sc_root: str | Path | None = None) -> Path:
    return Path(sc_root).expanduser().resolve() if sc_root else DEFAULT_SC_RELATIVE_ROOT.resolve()


def resolve_ygg_root(ygg_root: str | Path | None = None) -> Path:
    return Path(ygg_root).expanduser().resolve() if ygg_root else DEFAULT_YGG_ROOT.resolve()


def frontier_registry_path(ygg_root: str | Path | None = None) -> Path:
    return resolve_ygg_root(ygg_root) / FRONTIER_REGISTRY_RELATIVE_PATH


def resolve_workspace_root(workspace_root: str | Path | None = None) -> Path:
    return Path(workspace_root).expanduser().resolve() if workspace_root else DEFAULT_ASSISTANT_WORKSPACE.resolve()


def frontier_queue_path(ygg_root: str | Path | None = None) -> Path:
    return resolve_ygg_root(ygg_root) / FRONTIER_QUEUE_RELATIVE_PATH


def load_frontier_registry(ygg_root: str | Path | None = None) -> dict[str, Any]:
    path = frontier_registry_path(ygg_root)
    if not path.exists():
        raise FileNotFoundError(f"Frontier registry does not exist: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Frontier registry `{path}` must contain a JSON object.")
    rows = payload.get("frontiers")
    if not isinstance(rows, list):
        raise ValueError(f"Frontier registry `{path}` is missing list field `frontiers`.")
    return payload


def load_frontier_queue(ygg_root: str | Path | None = None) -> dict[str, Any]:
    path = frontier_queue_path(ygg_root)
    if not path.exists():
        return {
            "version": 1,
            "updatedAt": None,
            "workspaceRoot": None,
            "domain": "ygg-dev",
            "activeFrontierId": None,
            "frontiers": [],
        }
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Frontier queue `{path}` must contain a JSON object.")
    rows = payload.get("frontiers")
    if not isinstance(rows, list):
        raise ValueError(f"Frontier queue `{path}` is missing list field `frontiers`.")
    return payload


def save_frontier_queue(payload: dict[str, Any], ygg_root: str | Path | None = None) -> Path:
    path = frontier_queue_path(ygg_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _registry_targets(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for row in registry.get("frontiers") or []:
        if not isinstance(row, dict):
            continue
        target = row.get("target")
        if not isinstance(target, dict):
            continue
        target_id = target.get("id")
        if isinstance(target_id, str) and target_id.strip():
            mapping[target_id] = row
    return mapping


def _queue_targets(queue: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for row in queue.get("frontiers") or []:
        if not isinstance(row, dict):
            continue
        frontier_id = row.get("id")
        if isinstance(frontier_id, str) and frontier_id.strip():
            mapping[frontier_id] = row
    return mapping


def discover_current_frontier_note(sc_root: str | Path | None = None) -> Path | None:
    root = resolve_sc_root(sc_root)
    plans_dir = root / "plans"
    if not plans_dir.exists():
        return None
    notes = sorted(plans_dir.glob("today_frontier_*.md"))
    if not notes:
        return None
    return notes[-1]


def _strip_scalar(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {'"', "'"}:
        return cleaned[1:-1]
    return cleaned


def _parse_baton(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    meta: dict[str, Any] = {}
    body_start = 0
    if lines and lines[0].strip() == "---":
        idx = 1
        while idx < len(lines) and lines[idx].strip() != "---":
            line = lines[idx]
            if ":" in line:
                key, raw = line.split(":", 1)
                meta[key.strip()] = _strip_scalar(raw)
            idx += 1
        body_start = idx + 1 if idx < len(lines) else idx

    sections: dict[str, str] = {}
    current: str | None = None
    buffer: list[str] = []
    for line in lines[body_start:]:
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            if current is not None:
                sections[current] = "\n".join(buffer).strip()
            current = match.group(1).strip().lower()
            buffer = []
            continue
        if current is not None:
            buffer.append(line)
    if current is not None:
        sections[current] = "\n".join(buffer).strip()

    return {"meta": meta, "sections": sections}


def _priority_rank(priority: str | None) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(str(priority or "medium").lower(), 3)


def _queue_status_rank(status: str | None) -> int:
    return {
        "active": 0,
        "ready": 1,
        "idea": 2,
        "waiting": 3,
        "blocked": 4,
        "done": 5,
        "dropped": 6,
    }.get(str(status or "ready").lower(), 9)


def _parse_updated_at(value: str | None) -> datetime:
    if not value:
        return datetime.fromtimestamp(0, tz=UTC)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return datetime.fromtimestamp(0, tz=UTC)


def _derive_queue_status(*, baton_status: str | None, active_task_file: str | None, baton_relative: str, existing_status: str | None) -> str:
    existing = str(existing_status or "").strip().lower()
    baton = str(baton_status or "").strip().lower()
    if baton == "done":
        return "done"
    if baton in {"blocked", "waiting", "dropped"}:
        return baton
    if active_task_file and (baton_relative == active_task_file or baton_relative.endswith(active_task_file)):
        return "active"
    if existing in {"idea", "waiting", "blocked", "dropped"}:
        return existing
    return "ready"


def sync_frontier_queue(
    workspace_root: str | Path | None = None,
    *,
    ygg_root: str | Path | None = None,
    domain: str = "ygg-dev",
) -> dict[str, Any]:
    workspace = resolve_workspace_root(workspace_root)
    queue = load_frontier_queue(ygg_root)
    existing = {row.get("id"): row for row in queue.get("frontiers") or [] if isinstance(row, dict)}

    index_path = workspace / "state" / "resume" / "index.json"
    active_task_file: str | None = None
    if index_path.exists():
        index_payload = json.loads(index_path.read_text(encoding="utf-8"))
        domain_row = (index_payload.get("domains") or {}).get(domain) or {}
        active_task_file = domain_row.get("activeTaskFile")

    tasks_dir = workspace / "state" / "resume" / "tasks"
    rows: list[dict[str, Any]] = []
    for path in sorted(tasks_dir.glob(f"{domain}--*.md")):
        parsed = _parse_baton(path)
        meta = parsed["meta"]
        sections = parsed["sections"]
        task_id = str(meta.get("taskId") or path.stem.replace(f"{domain}--", "")).strip()
        frontier_id = f"frontier-task:{domain}:{task_id}"
        relative = str(path.relative_to(workspace))
        previous = existing.get(frontier_id) or {}
        baton_status = str(meta.get("status") or "unknown").strip().lower()
        queue_status = _derive_queue_status(
            baton_status=baton_status,
            active_task_file=active_task_file,
            baton_relative=relative,
            existing_status=previous.get("queueStatus"),
        )
        rows.append({
            "id": frontier_id,
            "title": meta.get("title") or task_id,
            "domain": domain,
            "task": task_id,
            "batonFile": relative,
            "queueStatus": queue_status,
            "batonStatus": baton_status,
            "priority": str(meta.get("priority") or previous.get("priority") or "medium").lower(),
            "updatedAt": meta.get("updatedAt") or previous.get("updatedAt"),
            "objective": sections.get("objective", ""),
            "currentState": sections.get("current state", ""),
            "nextAction": sections.get("next action", ""),
            "selectionReason": previous.get("selectionReason") or (
                "Current active Ygg baton in assistant-home." if queue_status == "active" else "Imported from assistant-home Ygg task baton."
            ),
            "openedCount": int(previous.get("openedCount") or 0),
            "lastOpenedAt": previous.get("lastOpenedAt"),
            "dependsOn": previous.get("dependsOn") or [],
            "blockedBy": previous.get("blockedBy") or [],
            "source": "assistant-home-baton",
        })

    rows.sort(key=lambda row: (
        _queue_status_rank(row.get("queueStatus")),
        _priority_rank(row.get("priority")),
        -_parse_updated_at(row.get("updatedAt")).timestamp(),
        str(row.get("title") or ""),
    ))

    active_frontier_id = next((row["id"] for row in rows if row.get("queueStatus") == "active"), None)
    payload = {
        "version": 1,
        "updatedAt": datetime.now(UTC).isoformat(),
        "workspaceRoot": str(workspace),
        "domain": domain,
        "activeFrontierId": active_frontier_id,
        "frontiers": rows,
    }
    path = save_frontier_queue(payload, ygg_root)
    return {
        "schema": "ygg-frontier-queue-sync/v1",
        "generatedAt": payload["updatedAt"],
        "queuePath": str(path),
        "workspaceRoot": str(workspace),
        "domain": domain,
        "activeFrontierId": active_frontier_id,
        "count": len(rows),
        "frontiers": rows,
    }


def list_frontier_queue(ygg_root: str | Path | None = None) -> dict[str, Any]:
    queue = load_frontier_queue(ygg_root)
    rows = [row for row in queue.get("frontiers") or [] if isinstance(row, dict)]
    rows.sort(key=lambda row: (
        _queue_status_rank(row.get("queueStatus")),
        _priority_rank(row.get("priority")),
        -_parse_updated_at(row.get("updatedAt")).timestamp(),
        str(row.get("title") or ""),
    ))
    return {
        "schema": "ygg-frontier-queue/v1",
        "generatedAt": datetime.now(UTC).isoformat(),
        "queue": {
            "path": str(frontier_queue_path(ygg_root)),
            "updatedAt": queue.get("updatedAt"),
            "workspaceRoot": queue.get("workspaceRoot"),
            "domain": queue.get("domain") or "ygg-dev",
            "activeFrontierId": queue.get("activeFrontierId"),
        },
        "count": len(rows),
        "items": rows,
    }


def resolve_queue_frontier_target(
    target: str | None = None,
    *,
    ygg_root: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    queue = load_frontier_queue(ygg_root)
    rows = [row for row in queue.get("frontiers") or [] if isinstance(row, dict)]
    if not rows:
        return None

    requested = (target or "current").strip()
    target_map = _queue_targets(queue)
    active_frontier_id = queue.get("activeFrontierId")

    if requested in {"", "current", "active", "frontier"}:
        if isinstance(active_frontier_id, str) and active_frontier_id in target_map:
            return target_map[active_frontier_id], queue
        for preferred_status in ("active", "ready", "idea", "waiting", "blocked"):
            for row in rows:
                if row.get("queueStatus") == preferred_status:
                    return row, queue
        return rows[0], queue

    for row in rows:
        if requested in {row.get("id"), row.get("task"), f"{row.get('domain')}:{row.get('task')}", row.get("batonFile")}:
            return row, queue
    return None


def mark_queue_frontier_active(frontier_id: str, *, ygg_root: str | Path | None = None) -> dict[str, Any]:
    queue = load_frontier_queue(ygg_root)
    rows = [row for row in queue.get("frontiers") or [] if isinstance(row, dict)]
    now = datetime.now(UTC).isoformat()
    found = False
    for row in rows:
        if row.get("id") == frontier_id:
            row["queueStatus"] = "active"
            row["openedCount"] = int(row.get("openedCount") or 0) + 1
            row["lastOpenedAt"] = now
            found = True
        elif row.get("queueStatus") == "active" and row.get("batonStatus") != "done":
            row["queueStatus"] = "ready"
    if not found:
        raise KeyError(f"Unknown frontier queue id `{frontier_id}`")
    queue["updatedAt"] = now
    queue["activeFrontierId"] = frontier_id
    save_frontier_queue(queue, ygg_root)
    return queue


def _deep_copy(value: Any) -> Any:
    return json.loads(json.dumps(value))


def _exists_rel(root: Path, relative: str) -> bool:
    return (root / relative).exists()


def _quality_level(*, docs: bool, artifacts: bool, validation: bool, traceability: bool) -> dict[str, str]:
    def level(flag: bool) -> str:
        return "strong" if flag else "partial"

    return {
        "documentation": level(docs),
        "implementation": "partial" if artifacts else "weak",
        "validation": "partial" if validation else "weak",
        "traceability": level(traceability),
    }


def list_frontiers(
    sc_root: str | Path | None = None,
    *,
    ygg_root: str | Path | None = None,
) -> dict[str, Any]:
    root = resolve_sc_root(sc_root)
    registry = load_frontier_registry(ygg_root)
    default_target = registry.get("defaultTarget")
    rows: list[dict[str, Any]] = []

    for row in registry.get("frontiers") or []:
        if not isinstance(row, dict):
            continue
        target = row.get("target") or {}
        summary = row.get("summary") or {}
        promotion = row.get("promotion") or {}
        next_move = row.get("nextMove") or {}
        target_id = target.get("id")
        if not isinstance(target_id, str) or not target_id.strip():
            continue

        evidence = _build_evidence(root, row)
        audit_verdict = summary.get("auditVerdict") or "unknown"
        readiness = promotion.get("readiness") or "unknown"
        if evidence.get("benchmarkResultExists"):
            audit_verdict = "grounded"
            readiness = "reviewable"

        gap_count = sum(
            len(row.get("gaps", {}).get(section) or [])
            for section in ("blockingGaps", "missingBenchmarks", "missingArtifacts", "missingNullModels")
        )

        rows.append(
            {
                "id": target_id,
                "title": target.get("title") or target_id,
                "status": target.get("status") or "unknown",
                "claimTier": target.get("claimTier") or "unknown",
                "ownerSurface": target.get("ownerSurface") or "unknown",
                "default": target_id == default_target,
                "loadBearing": bool(summary.get("loadBearing")),
                "auditVerdict": audit_verdict,
                "promotionReadiness": readiness,
                "objective": summary.get("objective") or "",
                "operatorReading": summary.get("operatorReading") or "",
                "nextMoveType": next_move.get("type") or "",
                "nextMoveAction": next_move.get("action") or "",
                "gapCount": gap_count,
                "evidence": {
                    "docs": len(evidence.get("docs") or []),
                    "artifacts": len(evidence.get("artifacts") or []),
                    "tests": len(evidence.get("tests") or []),
                    "benchmarks": len(evidence.get("benchmarks") or []),
                    "benchmarkResultExists": bool(evidence.get("benchmarkResultExists")),
                },
            }
        )

    def _sort_key(item: dict[str, Any]) -> tuple[int, int, int, str]:
        status_rank = {"active": 0, "partial": 1, "pressure-testing": 2, "planned": 3, "speculative": 4, "implemented": 5}
        readiness_rank = {"promotion-candidate": 0, "reviewable": 1, "evidence-needed": 2, "not-ready": 3}
        verdict_rank = {"grounded": 0, "mixed": 1, "under-founded": 2, "blocked": 3, "unclear": 4}
        return (
            0 if item.get("default") else 1,
            status_rank.get(str(item.get("status")), 9),
            readiness_rank.get(str(item.get("promotionReadiness")), verdict_rank.get(str(item.get("auditVerdict")), 9)),
            str(item.get("title", "")),
        )

    rows.sort(key=_sort_key)
    return {
        "schema": "ygg-frontier-list/v1",
        "generatedAt": datetime.now(UTC).isoformat(),
        "scRoot": str(root),
        "registry": {
            "path": str(frontier_registry_path(ygg_root)),
            "version": registry.get("version"),
            "updatedAt": registry.get("updatedAt"),
            "defaultTarget": default_target,
        },
        "count": len(rows),
        "items": rows,
    }


def resolve_frontier_target(
    target: str | None = None,
    *,
    ygg_root: str | Path | None = None,
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    registry = load_frontier_registry(ygg_root)
    target_map = _registry_targets(registry)
    default_target = registry.get("defaultTarget")
    requested = (target or "current").strip()

    if requested in {"", "current", "active", "frontier"}:
        effective_target = default_target
    else:
        effective_target = requested

    if not isinstance(effective_target, str) or effective_target not in target_map:
        known = ", ".join(sorted(target_map))
        raise KeyError(f"Unsupported frontier audit target `{requested}`. Known targets: {known}")

    return effective_target, target_map[effective_target], registry


def current_frontier_payload(
    sc_root: str | Path | None = None,
    *,
    ygg_root: str | Path | None = None,
) -> dict[str, Any]:
    root = resolve_sc_root(sc_root)
    note = discover_current_frontier_note(root)
    queue_match = resolve_queue_frontier_target("current", ygg_root=ygg_root)
    if queue_match is not None:
        queue_row, queue = queue_match
        return {
            "schema": "ygg-frontier-current/v1",
            "generatedAt": datetime.now(UTC).isoformat(),
            "scRoot": str(root),
            "registry": {
                "path": str(frontier_queue_path(ygg_root)),
                "version": queue.get("version"),
                "updatedAt": queue.get("updatedAt"),
            },
            "target": {
                "id": queue_row["id"],
                "title": queue_row["title"],
            },
            "frontierNote": queue_row.get("batonFile"),
            "reason": "Current frontier is resolved from the Ygg frontier queue, which promotes assistant-home Ygg batons into one active or ready frontier slot.",
        }

    effective_target, frontier_row, registry = resolve_frontier_target("current", ygg_root=ygg_root)
    return {
        "schema": "ygg-frontier-current/v1",
        "generatedAt": datetime.now(UTC).isoformat(),
        "scRoot": str(root),
        "registry": {
            "path": str(frontier_registry_path(ygg_root)),
            "version": registry.get("version"),
            "updatedAt": registry.get("updatedAt"),
        },
        "target": {
            "id": effective_target,
            "title": frontier_row["target"]["title"],
        },
        "frontierNote": str(note.relative_to(root)) if note else None,
        "reason": "Current frontier is resolved from the Ygg frontier registry, with the latest today_frontier note attached as additional context.",
    }


def _build_evidence(root: Path, frontier_row: dict[str, Any]) -> dict[str, Any]:
    plan = frontier_row.get("evidencePlan") or {}
    doc_paths = [item for item in plan.get("docs") or [] if isinstance(item, str)]
    artifact_paths = [item for item in plan.get("artifacts") or [] if isinstance(item, str)]
    test_paths = [item for item in plan.get("tests") or [] if isinstance(item, str)]
    benchmark_paths = [item for item in plan.get("benchmarks") or [] if isinstance(item, str)]
    concept_ids = [item for item in plan.get("spineConcepts") or [] if isinstance(item, str)]
    pressure_ids = [item for item in plan.get("pressureEvents") or [] if isinstance(item, str)]
    pressure_paths = [item for item in plan.get("pressureEventPaths") or [] if isinstance(item, str)]
    benchmark_result_candidates = [item for item in plan.get("benchmarkResultCandidates") or [] if isinstance(item, str)]

    benchmark_results_exist = any(_exists_rel(root, relative) for relative in benchmark_result_candidates)
    evidence = {
        "docs": [relative for relative in doc_paths if _exists_rel(root, relative)],
        "artifacts": [relative for relative in artifact_paths if _exists_rel(root, relative)],
        "tests": [relative for relative in test_paths if _exists_rel(root, relative)],
        "benchmarks": [relative for relative in benchmark_paths if _exists_rel(root, relative)],
        "matrixRows": [item for item in frontier_row.get("matrixRows") or [] if isinstance(item, str)],
        "spineConcepts": [concept for concept in concept_ids if _exists_rel(root, f"spine/concepts/{concept}.yaml")],
        "pressureEvents": [pressure for pressure, path in zip(pressure_ids, pressure_paths, strict=False) if _exists_rel(root, path)],
        "quality": _quality_level(
            docs=all(_exists_rel(root, relative) for relative in doc_paths) if doc_paths else False,
            artifacts=any(_exists_rel(root, relative) for relative in artifact_paths),
            validation=benchmark_results_exist or any(_exists_rel(root, relative) for relative in test_paths),
            traceability=all(_exists_rel(root, f"spine/concepts/{concept}.yaml") for concept in concept_ids) if concept_ids else False,
        ),
        "benchmarkResultExists": benchmark_results_exist,
        "benchmarkResultCandidates": benchmark_result_candidates,
    }
    return evidence


def _build_sources(root: Path, frontier_row: dict[str, Any], evidence: dict[str, Any], latest_frontier: Path | None) -> list[dict[str, Any]]:
    sources = [
        AuditSource(
            path=relative,
            kind=("doc" if relative.endswith(".md") else "yaml"),
            authority="canonical",
            used_for=["target", "foundations", "evidence", "dependencies"],
        ).to_dict()
        for relative in evidence.get("docs") or []
    ]

    if latest_frontier is not None:
        latest_rel = str(latest_frontier.relative_to(root))
        if latest_rel not in {row["path"] for row in sources}:
            sources.append(
                AuditSource(
                    path=latest_rel,
                    kind="doc",
                    authority="canonical",
                    used_for=["summary", "dependencies"],
                ).to_dict()
            )

    sources.append(
        AuditSource(
            path=str(FRONTIER_REGISTRY_RELATIVE_PATH),
            kind="json",
            authority="derived",
            used_for=["target", "summary", "foundations", "gaps", "dependencies", "promotion", "nextMove"],
        ).to_dict()
    )
    return sources


def frontier_open_payload(
    sc_root: str | Path | None = None,
    target: str | None = None,
    *,
    ygg_root: str | Path | None = None,
) -> dict[str, Any]:
    root = resolve_sc_root(sc_root)
    queue_match = resolve_queue_frontier_target(target, ygg_root=ygg_root)
    if queue_match is not None:
        queue_row, queue = queue_match
        handoff = {
            "mode": "resume",
            "domain": queue_row.get("domain") or "ygg-dev",
            "task": queue_row.get("task") or "",
            "why": queue_row.get("selectionReason") or "Open the selected Ygg frontier baton.",
            "request": queue_row.get("nextAction") or queue_row.get("objective") or queue_row.get("title") or queue_row.get("id") or "Continue the frontier.",
        }
        command = ["ygg", "resume", str(handoff["domain"]), str(handoff["task"])]
        return {
            "schema": "ygg-frontier-open/v1",
            "generatedAt": datetime.now(UTC).isoformat(),
            "scRoot": str(root),
            "registry": {
                "path": str(frontier_queue_path(ygg_root)),
                "version": queue.get("version"),
                "updatedAt": queue.get("updatedAt"),
            },
            "target": {
                "id": queue_row.get("id") or "current",
                "title": queue_row.get("title") or queue_row.get("task") or "current frontier",
                "status": queue_row.get("queueStatus") or "unknown",
                "claimTier": queue_row.get("priority") or "queue",
            },
            "frontierNote": queue_row.get("batonFile"),
            "summary": {
                "objective": queue_row.get("objective") or "",
                "auditVerdict": "queue-selected",
                "operatorReading": queue_row.get("selectionReason") or "Imported from assistant-home Ygg frontier queue.",
            },
            "nextMove": {
                "type": "resume-task",
                "action": queue_row.get("nextAction") or "Resume the selected Ygg frontier.",
                "why": "Frontier queue chooses one active or ready baton at a time.",
            },
            "handoff": handoff,
            "openDecision": {
                "mode": "resume",
                "command": command,
                "launchHint": "Resume the selected Ygg frontier from the synced assistant-home baton queue.",
                "reason": handoff["why"],
            },
        }

    effective_target, frontier_row, registry = resolve_frontier_target(target, ygg_root=ygg_root)
    latest_frontier = discover_current_frontier_note(root)
    handoff = _deep_copy(frontier_row.get("handoff") or {})
    summary = _deep_copy(frontier_row.get("summary") or {})
    next_move = _deep_copy(frontier_row.get("nextMove") or {})
    target_row = _deep_copy(frontier_row.get("target") or {})

    if not handoff:
        handoff = {
            "mode": "root",
            "why": "No explicit frontier handoff is registered yet, so the safest posture is to enter the planner with frontier context rather than guessing a lane.",
            "request": f"Work the frontier `{effective_target}` carefully. Objective: {summary.get('objective') or 'advance the frontier'}. Next move: {next_move.get('action') or 'decide the next rigorous step'}."
        }

    command: list[str]
    launch_hint: str
    if handoff.get("mode") == "resume" and handoff.get("domain") and handoff.get("task"):
        command = ["ygg", "resume", str(handoff["domain"]), str(handoff["task"])]
        launch_hint = "Resume the existing frontier-aligned lane."
    elif handoff.get("mode") == "branch" and handoff.get("domain") and handoff.get("task"):
        command = [
            "ygg", "branch", str(handoff["domain"]), str(handoff["task"]),
            "--objective", str(summary.get("objective") or target_row.get("title") or effective_target),
            "--next-action", str(next_move.get("action") or "Continue the frontier."),
        ]
        launch_hint = "Create a fresh tracked lane for the frontier."
    else:
        request = str(handoff.get("request") or next_move.get("action") or summary.get("objective") or effective_target)
        command = ["ygg", "root", request]
        launch_hint = "Open the planner with frontier context instead of forcing a lane guess."

    return {
        "schema": "ygg-frontier-open/v1",
        "generatedAt": datetime.now(UTC).isoformat(),
        "scRoot": str(root),
        "registry": {
            "path": str(frontier_registry_path(ygg_root)),
            "version": registry.get("version"),
            "updatedAt": registry.get("updatedAt"),
        },
        "target": {
            "id": effective_target,
            "title": target_row.get("title") or effective_target,
            "status": target_row.get("status") or "unknown",
            "claimTier": target_row.get("claimTier") or "unknown",
        },
        "frontierNote": str(latest_frontier.relative_to(root)) if latest_frontier else None,
        "summary": {
            "objective": summary.get("objective") or "",
            "auditVerdict": summary.get("auditVerdict") or "unknown",
            "operatorReading": summary.get("operatorReading") or "",
        },
        "nextMove": next_move,
        "handoff": handoff,
        "openDecision": {
            "mode": handoff.get("mode") or "root",
            "command": command,
            "launchHint": launch_hint,
            "reason": handoff.get("why") or "",
        },
    }


def build_frontier_audit(
    sc_root: str | Path | None = None,
    target: str | None = None,
    *,
    ygg_root: str | Path | None = None,
) -> dict[str, Any]:
    root = resolve_sc_root(sc_root)
    effective_target, frontier_row, registry = resolve_frontier_target(target, ygg_root=ygg_root)
    latest_frontier = discover_current_frontier_note(root)
    evidence = _build_evidence(root, frontier_row)

    payload = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(UTC).isoformat(),
        "generator": "ygg frontier audit",
        "scRoot": str(root),
        "registry": {
            "path": str(frontier_registry_path(ygg_root)),
            "version": registry.get("version"),
            "updatedAt": registry.get("updatedAt"),
        },
        "target": _deep_copy(frontier_row["target"]),
        "summary": _deep_copy(frontier_row["summary"]),
        "foundations": _deep_copy(frontier_row["foundations"]),
        "evidence": evidence,
        "gaps": _deep_copy(frontier_row["gaps"]),
        "dependencies": _deep_copy(frontier_row["dependencies"]),
        "promotion": _deep_copy(frontier_row["promotion"]),
        "nextMove": _deep_copy(frontier_row["nextMove"]),
        "sources": _build_sources(root, frontier_row, evidence, latest_frontier),
    }

    payload["target"]["id"] = effective_target

    if latest_frontier is not None:
        payload["summary"]["whyNow"] = (
            payload["summary"]["whyNow"]
            + f" Latest frontier note: {latest_frontier.relative_to(root)}."
        )

    if evidence.get("benchmarkResultExists"):
        payload["summary"]["auditVerdict"] = "grounded"
        payload["summary"]["operatorReading"] = (
            "The frontier now has a benchmark result artifact attached, so the next decision can be made on comparative evidence rather than only on framing quality."
        )
        payload["promotion"]["readiness"] = "reviewable"
        payload["promotion"]["why"] = (
            "A benchmark result artifact exists, so the next decision can be made on evidence rather than plan quality alone."
        )
        payload["gaps"]["missingBenchmarks"] = [
            item
            for item in payload["gaps"].get("missingBenchmarks") or []
            if "not yet executed" not in item
        ]

    return payload
