from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ygg.runtime_notes import append_daily_block, ensure_dir

DEFAULT_DAILY_DIR = "state/notes/daily"
DEFAULT_PROMOTION_FILE = "state/runtime/promotion-candidates.jsonl"


def load_event_from_args(event_json: str | None, event_file: str | None) -> dict[str, Any]:
    if event_json:
        return json.loads(event_json)
    if event_file:
        return json.loads(Path(event_file).read_text(encoding="utf-8"))
    raise ValueError("Either --event-json or --event-file is required")


def build_daily_bullets(event: dict[str, Any]) -> list[str]:
    bullets: list[str] = []
    summary = event.get("summary")
    source = event.get("source")
    importance = event.get("importance")
    if summary:
        bullets.append(f"summary: {summary}")
    if source:
        bullets.append(f"source: {source}")
    if importance:
        bullets.append(f"importance: {importance}")

    details = event.get("details") or {}
    changes = details.get("changes") if isinstance(details, dict) else None
    if isinstance(changes, list):
        for change in changes:
            if not isinstance(change, dict):
                continue
            field = change.get("field", "(field)")
            old = change.get("old")
            new = change.get("new")
            old_s = "(unset)" if old in (None, "") else str(old)
            new_s = "(unset)" if new in (None, "") else str(new)
            bullets.append(f"change {field}: {old_s} -> {new_s}")

    if isinstance(details, dict):
        for key, value in details.items():
            if key == "changes":
                continue
            if isinstance(value, (dict, list)):
                rendered = json.dumps(value, sort_keys=True)
            else:
                rendered = str(value)
            bullets.append(f"{key}: {rendered}")

    return bullets


def build_promotion_candidate(event: dict[str, Any]) -> dict[str, Any]:
    event_id = event.get("id")
    timestamp = event.get("timestamp")
    details = event.get("details") or {}
    links = event.get("links") or {}
    return {
        "id": f"promo:{event_id}" if event_id else None,
        "timestamp": timestamp,
        "sourceEventId": event_id,
        "kind": "memory.candidate.created",
        "status": "candidate",
        "importance": event.get("importance", "routine"),
        "summary": event.get("summary", "(no summary)"),
        "source": event.get("source"),
        "eventKind": event.get("kind"),
        "whyItMayBeDurable": [
            "This event was explicitly routed for promotion review.",
            "It may represent a durable continuity, architecture, or operational milestone.",
        ],
        "promotionTarget": "core/MEMORY.md",
        "evidence": {
            "details": details,
            "links": links,
        },
        "review": {
            "recommendedAction": "human-review",
            "reviewAfter": timestamp,
        },
    }


def append_promotion_candidate(path: Path, event: dict[str, Any]) -> Path:
    ensure_dir(path.parent)
    candidate = build_promotion_candidate(event)
    candidate_id = candidate.get("id")

    existing_ids: set[str] = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            existing_id = payload.get("id")
            if isinstance(existing_id, str):
                existing_ids.add(existing_id)

    if candidate_id and candidate_id in existing_ids:
        return path

    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(candidate, separators=(",", ":")) + "\n")
    return path


def route_event(
    workspace: Path,
    event: dict[str, Any],
    *,
    daily_dir: str = DEFAULT_DAILY_DIR,
    promotion_file: str = DEFAULT_PROMOTION_FILE,
    dry_run: bool = False,
) -> dict[str, Any]:
    route = event.get("route") or {}
    kind = event.get("kind", "event")
    heading = f"Ratatoskr - {kind}"
    result: dict[str, Any] = {
        "daily": None,
        "promotion": None,
        "summary": f"Ratatoskr routed {kind}",
        "eventId": event.get("id"),
    }

    if route.get("daily"):
        bullets = build_daily_bullets(event)
        if not dry_run:
            daily_path = append_daily_block(
                workspace / daily_dir,
                heading=heading,
                bullet_lines=bullets,
            )
            result["daily"] = str(daily_path)
        else:
            result["daily"] = str(workspace / daily_dir)

    if route.get("promote"):
        promo_path = workspace / promotion_file
        if not dry_run:
            written = append_promotion_candidate(promo_path, event)
            result["promotion"] = str(written)
        else:
            result["promotion"] = str(promo_path)

    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ratatoskr continuity courier")
    parser.add_argument(
        "--workspace",
        default=str(Path(__file__).resolve().parents[2]),
        help="Workspace root (defaults to the Ygg repo root).",
    )
    parser.add_argument("--event-json", help="Inline JSON event payload.")
    parser.add_argument("--event-file", help="Path to JSON event payload.")
    parser.add_argument("--daily-dir", default=DEFAULT_DAILY_DIR)
    parser.add_argument("--promotion-file", default=DEFAULT_PROMOTION_FILE)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--show-event", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    workspace = Path(args.workspace).resolve()
    event = load_event_from_args(args.event_json, args.event_file)
    result = route_event(
        workspace,
        event,
        daily_dir=args.daily_dir,
        promotion_file=args.promotion_file,
        dry_run=args.dry_run,
    )
    if args.show_event:
        print(json.dumps(event, indent=2))
    else:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
