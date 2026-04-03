from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ygg.runtime_notes import append_daily_block, ensure_dir

DEFAULT_DAILY_DIR = "state/notes/daily"
DEFAULT_PROMOTION_FILE = "state/notes/promotion-candidates.md"


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


def append_promotion_candidate(path: Path, event: dict[str, Any]) -> Path:
    ensure_dir(path.parent)
    heading = f"## {event.get('kind', 'event')} - {event.get('summary', '(no summary)')}"
    lines = [heading]
    if event.get("source"):
        lines.append(f"- source: {event['source']}")
    if event.get("importance"):
        lines.append(f"- importance: {event['importance']}")
    details = event.get("details") or {}
    if details:
        lines.append("- details:")
        for key, value in details.items():
            if isinstance(value, (dict, list)):
                rendered = json.dumps(value, sort_keys=True)
            else:
                rendered = str(value)
            lines.append(f"  - {key}: {rendered}")
    block = "\n".join(lines) + "\n\n"

    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if existing.endswith(block):
        return path
    path.write_text(existing + block, encoding="utf-8")
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
