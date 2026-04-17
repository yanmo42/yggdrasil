"""
work_resolver — continuity brief assembly for ygg work.

Single exported function: resolve_continuity_brief(root, request, *, context)

Reads the latest checkpoint, active programs/ideas from the semantic registry,
optionally runs topology retrieval on a NL request, and returns a structured
brief with a dispatch recommendation.

Degrades gracefully — never raises. If state is missing, status="empty".
"""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any


_IMPL_WORDS = (
    "implement",
    "build",
    "fix",
    "code",
    "wire up",
    "create",
    "add",
    "write",
)

_DISPATCH_THRESHOLD = 0.65
_DROP_CONFIDENCE_PENALTY = 0.2
_FRESH_CHECKPOINT_DAYS = 7
_FRESH_CHECKPOINT_BONUS = 0.2
_PROGRAM_LANE_MATCH_BONUS = 0.1
_CWD_MATCH_BONUS = 0.1


def _days_since(timestamp_str: str) -> float:
    """Return age in days since ISO timestamp. Returns large number on parse error."""
    try:
        dt = datetime.fromisoformat(timestamp_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return (datetime.now(UTC) - dt).total_seconds() / 86400.0
    except Exception:
        return 9999.0


def _try_retrieve(root: Path, query: str) -> dict[str, Any] | None:
    """Run topology retrieval, returning None on any failure."""
    try:
        from ygg.continuity_retrieval import retrieve_continuity

        return retrieve_continuity(root, query, strategy="topology", limit=3)
    except Exception:
        return None


def _load_checkpoint(root: Path):
    """Load latest checkpoint, returning None on any failure."""
    try:
        from ygg.continuity import load_latest_checkpoint

        return load_latest_checkpoint(root)
    except Exception:
        return None


def _load_registry_items(root: Path, kind: str) -> list[dict[str, Any]]:
    """Load registry items, returning empty list on any failure."""
    try:
        from ygg.semantic_registry import list_registry_items

        payload = list_registry_items(root, kind)
        return list(payload.get("items") or [])
    except Exception:
        return []


def resolve_continuity_brief(
    root: str | Path,
    request: str,
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Assemble a continuity brief for ygg work.

    Args:
        root: Ygg repo root.
        request: NL request string (may be empty).
        context: Optional context dict from _gather_work_context (cwd_project, etc.).

    Returns dict with keys:
        status            "active" | "resumable" | "empty"
        confidence        float 0.0–1.0
        latestCheckpoint  dict | None
        activeProgram     dict | None
        relatedIdeas      list[dict]
        matchedAnchor     dict | None
        suggestedDispatch "forge" | "resume" | "passthrough"
        dispatchReason    str
    """
    root_path = Path(root).expanduser().resolve()
    context = context or {}

    # ── 1. Load state ────────────────────────────────────────────────────────
    checkpoint = _load_checkpoint(root_path)

    programs = [
        p for p in _load_registry_items(root_path, "program")
        if p.get("status") == "active"
    ]
    ideas = [
        i for i in _load_registry_items(root_path, "idea")
        if i.get("status") in ("incubating", "testing")
    ]

    # ── 2. Retrieval anchor (only when request is non-empty) ─────────────────
    matched_anchor: dict[str, Any] | None = None
    if request:
        retrieval = _try_retrieve(root_path, request)
        if retrieval:
            for result in retrieval.get("results") or []:
                rec = result.get("record") or {}
                if rec.get("kind") in ("checkpoint", "program", "idea"):
                    matched_anchor = {
                        "kind": rec["kind"],
                        "id": rec.get("id", ""),
                        "title": rec.get("title", ""),
                        "summary": rec.get("summary", ""),
                    }
                    break

    # ── 3. Confidence scoring ─────────────────────────────────────────────────
    confidence = 0.5
    checkpoint_fresh = False
    checkpoint_disposition = ""

    if checkpoint:
        age_days = _days_since(checkpoint.timestamp)
        checkpoint_disposition = checkpoint.disposition
        if age_days < _FRESH_CHECKPOINT_DAYS:
            confidence += _FRESH_CHECKPOINT_BONUS
            checkpoint_fresh = True
        if checkpoint.disposition == "DROP_LOCAL":
            confidence -= _DROP_CONFIDENCE_PENALTY

    active_program = programs[0] if programs else None
    if active_program and checkpoint:
        prog_lanes = set(active_program.get("relatedLanes") or [])
        prog_id = active_program.get("id", "")
        cp_lane = checkpoint.lane or ""
        if cp_lane and (cp_lane in prog_lanes or cp_lane == prog_id or prog_id in cp_lane):
            confidence += _PROGRAM_LANE_MATCH_BONUS

    cwd_project = context.get("cwd_project")
    if isinstance(cwd_project, dict) and cwd_project.get("name") and active_program:
        proj_name = cwd_project["name"]
        prog_lanes = set(active_program.get("relatedLanes") or [])
        prog_id = active_program.get("id", "")
        if proj_name in prog_lanes or proj_name in prog_id or prog_id in proj_name:
            confidence += _CWD_MATCH_BONUS

    confidence = round(min(max(confidence, 0.0), 1.0), 3)

    # ── 4. Status ─────────────────────────────────────────────────────────────
    if active_program or checkpoint_fresh:
        status = "active"
    elif checkpoint:
        status = "resumable"
    else:
        status = "empty"

    # ── 5. Dispatch recommendation ────────────────────────────────────────────
    if confidence >= _DISPATCH_THRESHOLD and checkpoint_disposition != "DROP_LOCAL":
        req_lower = (request or "").lower()
        if any(w in req_lower for w in _IMPL_WORDS):
            suggested_dispatch = "forge"
            dispatch_reason = (
                f"confidence {confidence:.2f} >= {_DISPATCH_THRESHOLD} "
                "and request looks implementation-shaped"
            )
        else:
            suggested_dispatch = "resume"
            dispatch_reason = (
                f"confidence {confidence:.2f} >= {_DISPATCH_THRESHOLD}, "
                "checkpoint available"
            )
    else:
        suggested_dispatch = "passthrough"
        if checkpoint_disposition == "DROP_LOCAL":
            dispatch_reason = "latest checkpoint disposition is DROP_LOCAL — nothing to resume"
        elif confidence < _DISPATCH_THRESHOLD:
            dispatch_reason = (
                f"confidence {confidence:.2f} below threshold {_DISPATCH_THRESHOLD}"
            )
        else:
            dispatch_reason = "no active state found"

    # ── 6. Build output ───────────────────────────────────────────────────────
    checkpoint_dict: dict[str, Any] | None = None
    if checkpoint:
        checkpoint_dict = {
            "timestamp": checkpoint.timestamp,
            "lane": checkpoint.lane,
            "summary": checkpoint.summary,
            "disposition": checkpoint.disposition,
            "nextAction": checkpoint.next_action,
        }

    program_dict: dict[str, Any] | None = None
    if active_program:
        program_dict = {
            "id": active_program.get("id"),
            "title": active_program.get("title"),
            "priority": active_program.get("priority"),
            "nextAction": active_program.get("nextAction"),
        }

    idea_rows = [
        {
            "id": i.get("id"),
            "title": i.get("title"),
            "status": i.get("status"),
            "nextAction": i.get("nextAction"),
        }
        for i in ideas
    ]

    return {
        "status": status,
        "confidence": confidence,
        "latestCheckpoint": checkpoint_dict,
        "activeProgram": program_dict,
        "relatedIdeas": idea_rows,
        "matchedAnchor": matched_anchor,
        "suggestedDispatch": suggested_dispatch,
        "dispatchReason": dispatch_reason,
    }
