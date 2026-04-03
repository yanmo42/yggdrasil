from __future__ import annotations

from datetime import datetime
from pathlib import Path


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def now_iso_local() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def today_local() -> str:
    return datetime.now().astimezone().date().isoformat()


def time_local_hm() -> str:
    return datetime.now().astimezone().strftime("%H:%M")


def append_daily_block(daily_dir: Path, *, heading: str, bullet_lines: list[str]) -> Path:
    ensure_dir(daily_dir)
    daily_path = daily_dir / f"{today_local()}.md"

    rendered_lines = [f"## {time_local_hm()} {heading}", ""]
    rendered_lines.extend(f"- {line}" for line in bullet_lines)
    rendered_lines.append("")
    rendered_lines.append("")
    block = "\n".join(rendered_lines)

    existing = daily_path.read_text(encoding="utf-8") if daily_path.exists() else ""
    if existing.endswith(block):
        return daily_path

    daily_path.write_text(existing + block, encoding="utf-8")
    return daily_path
