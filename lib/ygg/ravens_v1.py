from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from uuid import uuid4


RAVEN_SUBDIRS = ("flights", "logs", "aviary", "returns", "grafts", "beaks")


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.strip().lower())
    return s.strip("-") or "untitled"


def _new_id(prefix: str) -> str:
    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    return f"{prefix}-{stamp}-{uuid4().hex[:6]}"


def raven_paths(state_runtime_dir: Path) -> dict[str, Path]:
    root = state_runtime_dir / "ravens"
    return {
        "root": root,
        "flights": root / "flights",
        "logs": root / "logs",
        "aviary": root / "aviary",
        "returns": root / "returns",
        "grafts": root / "grafts",
        "beaks": root / "beaks",
    }


def ensure_raven_dirs(state_runtime_dir: Path) -> dict[str, Path]:
    paths = raven_paths(state_runtime_dir)
    for key in RAVEN_SUBDIRS:
        paths[key].mkdir(parents=True, exist_ok=True)
    return paths


def parse_actors(raw: str | list[str] | None) -> list[str]:
    if raw is None:
        return ["huginn", "muninn"]

    if isinstance(raw, list):
        tokens = []
        for item in raw:
            tokens.extend(re.split(r"[\s,]+", item.strip()))
    else:
        tokens = re.split(r"[\s,]+", raw.strip())

    actors = [_slugify(tok) for tok in tokens if tok]
    # Keep stable order + dedupe
    out: list[str] = []
    seen: set[str] = set()
    for actor in actors:
        if actor in seen:
            continue
        seen.add(actor)
        out.append(actor)
    return out or ["huginn", "muninn"]


def _append_event(log_file: Path, event: dict) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")


def launch_flight(
    *,
    state_runtime_dir: Path,
    purpose: str,
    trigger: str,
    actors: list[str],
    initiated_by: str = "spine",
    flight_id: str | None = None,
) -> dict:
    paths = ensure_raven_dirs(state_runtime_dir)
    now = _now_iso()
    fid = flight_id or _new_id("RAVEN")

    flight_file = paths["flights"] / f"{fid}.json"
    log_file = paths["logs"] / f"{fid}.jsonl"

    commissioned = {
        "id": f"{fid}::commissioned",
        "flightId": fid,
        "phase": "commissioned",
        "actor": initiated_by,
        "timestamp": now,
        "trigger": trigger,
        "purpose": purpose,
        "action": "commission",
        "target": "raven-flight",
        "notes": "Flight commissioned by spine.",
    }
    launched = {
        "id": f"{fid}::launched",
        "flightId": fid,
        "phase": "launched",
        "actor": actors[0],
        "timestamp": now,
        "trigger": trigger,
        "purpose": purpose,
        "action": "launch",
        "target": "environment",
        "notes": "Initial launch event.",
    }

    _append_event(log_file, commissioned)
    _append_event(log_file, launched)

    flight = {
        "id": fid,
        "status": "launched",
        "trigger": trigger,
        "purpose": purpose,
        "actors": actors,
        "initiatedBy": initiated_by,
        "createdAt": now,
        "updatedAt": now,
        "logFile": str(log_file),
        "returnFile": None,
        "adjudication": None,
        "promotion": None,
    }
    flight_file.write_text(json.dumps(flight, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return flight


def _flight_file(state_runtime_dir: Path, flight_id: str) -> Path:
    paths = ensure_raven_dirs(state_runtime_dir)
    return paths["flights"] / f"{flight_id}.json"


def load_flight(state_runtime_dir: Path, flight_id: str) -> dict:
    file = _flight_file(state_runtime_dir, flight_id)
    if not file.exists():
        raise FileNotFoundError(f"Unknown flight id: {flight_id}")
    return json.loads(file.read_text(encoding="utf-8"))


def save_flight(state_runtime_dir: Path, flight: dict) -> None:
    flight_id = str(flight["id"])
    file = _flight_file(state_runtime_dir, flight_id)
    file.write_text(json.dumps(flight, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def list_flights(state_runtime_dir: Path) -> list[dict]:
    paths = ensure_raven_dirs(state_runtime_dir)
    rows: list[dict] = []
    for file in sorted(paths["flights"].glob("RAVEN-*.json")):
        try:
            payload = json.loads(file.read_text(encoding="utf-8"))
        except Exception:
            continue
        rows.append(payload)

    rows.sort(key=lambda row: str(row.get("updatedAt") or row.get("createdAt") or ""), reverse=True)
    return rows


def render_return_packet(
    *,
    flight: dict,
    claim_tier: str,
    adjudication: str,
    promotion: str,
    evidence: list[str],
    recommendation: str,
    failure_conditions: list[str],
) -> str:
    actors = flight.get("actors") or []
    objective = flight.get("purpose") or "(no objective recorded)"

    lines = [
        "---",
        f"id: {flight['id']}",
        "status: returned",
        "actors:",
    ]
    for actor in actors:
        lines.append(f"  - {actor}")
    lines.extend(
        [
            f"trigger: {flight.get('trigger', 'unknown')}",
            f"claim_tier: {claim_tier}",
            f"adjudication: {adjudication}",
            f"promotion: {promotion}",
            "---",
            "",
            "## Objective",
            objective,
            "",
            "## Evidence",
        ]
    )

    if evidence:
        lines.extend(f"- {item}" for item in evidence)
    else:
        lines.append("- (add concrete evidence refs)")

    lines.extend(
        [
            "",
            "## Interpretation",
            "- (summarize what the evidence means)",
            "",
            "## Failure conditions",
        ]
    )

    if failure_conditions:
        lines.extend(f"- {item}" for item in failure_conditions)
    else:
        lines.append("- (define what would falsify this recommendation)")

    lines.extend(
        [
            "",
            "## Recommendation",
            recommendation or "- (state next action)",
            "",
        ]
    )

    return "\n".join(lines)


def create_return_packet(
    *,
    state_runtime_dir: Path,
    flight_id: str,
    claim_tier: str,
    adjudication: str,
    promotion: str,
    evidence: list[str],
    recommendation: str,
    failure_conditions: list[str],
    overwrite: bool = False,
) -> dict:
    paths = ensure_raven_dirs(state_runtime_dir)
    flight = load_flight(state_runtime_dir, flight_id)

    return_file = paths["returns"] / f"{flight_id}.md"
    if return_file.exists() and not overwrite:
        raise FileExistsError(f"Return file already exists: {return_file}")

    markdown = render_return_packet(
        flight=flight,
        claim_tier=claim_tier,
        adjudication=adjudication,
        promotion=promotion,
        evidence=evidence,
        recommendation=recommendation,
        failure_conditions=failure_conditions,
    )
    return_file.write_text(markdown, encoding="utf-8")

    now = _now_iso()
    flight["status"] = "returned"
    flight["updatedAt"] = now
    flight["returnFile"] = str(return_file)
    flight["adjudication"] = adjudication
    flight["promotion"] = promotion
    save_flight(state_runtime_dir, flight)

    log_file = paths["logs"] / f"{flight_id}.jsonl"
    _append_event(
        log_file,
        {
            "id": f"{flight_id}::returned",
            "flightId": flight_id,
            "phase": "returned",
            "actor": "muninn",
            "timestamp": now,
            "trigger": flight.get("trigger", "unknown"),
            "purpose": flight.get("purpose", ""),
            "action": "return",
            "target": str(return_file),
            "notes": f"adjudication={adjudication}; promotion={promotion}",
        },
    )

    return {
        "id": flight_id,
        "returnFile": str(return_file),
        "adjudication": adjudication,
        "promotion": promotion,
        "status": "returned",
    }


def adjudicate_flight(
    *,
    state_runtime_dir: Path,
    flight_id: str,
    disposition: str,
) -> dict:
    paths = ensure_raven_dirs(state_runtime_dir)
    flight = load_flight(state_runtime_dir, flight_id)

    now = _now_iso()
    flight["status"] = disposition.lower()
    flight["updatedAt"] = now
    flight["adjudication"] = disposition
    save_flight(state_runtime_dir, flight)

    log_file = paths["logs"] / f"{flight_id}.jsonl"
    _append_event(
        log_file,
        {
            "id": f"{flight_id}::adjudicated",
            "flightId": flight_id,
            "phase": "adjudicated",
            "actor": "spine",
            "timestamp": now,
            "trigger": flight.get("trigger", "unknown"),
            "purpose": flight.get("purpose", ""),
            "action": "adjudicate",
            "target": disposition,
            "notes": f"disposition={disposition}",
        },
    )

    return {
        "id": flight_id,
        "status": flight["status"],
        "adjudication": disposition,
        "updatedAt": now,
    }


def propose_graft(
    *,
    state_runtime_dir: Path,
    title: str,
    target_attachment: str,
    why_now: str,
    risk_class: str,
    source_flight: str | None,
    proposal_id: str | None = None,
    overwrite: bool = False,
) -> dict:
    paths = ensure_raven_dirs(state_runtime_dir)
    gid = proposal_id or _new_id("GRAFT")
    file = paths["grafts"] / f"{gid}.md"
    if file.exists() and not overwrite:
        raise FileExistsError(f"Graft proposal already exists: {file}")

    now = _now_iso()
    lines = [
        "---",
        f"id: {gid}",
        "status: proposed",
        f"created_at: {now}",
        f"title: {title}",
        f"target_attachment: {target_attachment}",
        f"risk_class: {risk_class}",
        f"source_flight: {source_flight or 'none'}",
        "---",
        "",
        "## Why now",
        why_now or "- (state urgency and timing)",
        "",
        "## Inputs",
        "- (required inputs/resources)",
        "",
        "## Expected benefit",
        "- (what improves if adopted)",
        "",
        "## Failure conditions",
        "- (what would make this graft incorrect or unhelpful)",
        "",
        "## Adoption path",
        "- (trial plan, owner, and validation steps)",
        "",
    ]
    file.write_text("\n".join(lines), encoding="utf-8")

    return {
        "id": gid,
        "title": title,
        "targetAttachment": target_attachment,
        "riskClass": risk_class,
        "file": str(file),
    }


def propose_beak(
    *,
    state_runtime_dir: Path,
    title: str,
    beak_class: str,
    target: str,
    problem_type: str,
    evidence: list[str],
    source_flight: str | None,
    proposal_id: str | None = None,
    overwrite: bool = False,
) -> dict:
    paths = ensure_raven_dirs(state_runtime_dir)
    bid = proposal_id or _new_id("BEAK")
    file = paths["beaks"] / f"{bid}.md"
    if file.exists() and not overwrite:
        raise FileExistsError(f"Beak proposal already exists: {file}")

    now = _now_iso()
    lines = [
        "---",
        f"id: {bid}",
        "status: proposed",
        f"created_at: {now}",
        f"title: {title}",
        f"class: {beak_class}",
        f"target: {target}",
        f"problem_type: {problem_type}",
        f"source_flight: {source_flight or 'none'}",
        "execution: proposal-only",
        "---",
        "",
        "## Evidence",
    ]
    if evidence:
        lines.extend(f"- {item}" for item in evidence)
    else:
        lines.append("- (add decay/duplication/drift evidence)")

    lines.extend(
        [
            "",
            "## Suggested action",
            "- (describe proposed pruning/reshaping action)",
            "",
            "## Reversibility",
            "- (state whether action is reversible)",
            "",
            "## Approval required",
            f"- {'yes (hard beak)' if beak_class == 'hard' else 'yes/no per policy (soft beak)'}",
            "",
            "## Failure if not done",
            "- (what happens if this beak is ignored)",
            "",
        ]
    )

    file.write_text("\n".join(lines), encoding="utf-8")

    return {
        "id": bid,
        "title": title,
        "class": beak_class,
        "target": target,
        "problemType": problem_type,
        "file": str(file),
    }
