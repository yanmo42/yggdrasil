from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import socket
import subprocess
from typing import Any

from ygg.ratatoskr import DEFAULT_DAILY_DIR, route_event
from ygg.runtime_notes import append_daily_block, ensure_dir, now_iso_local

MEANINGFUL_FIELDS = [
    "timezone",
    "channel",
    "chatType",
    "runtimeCore",
    "sessionKey",
    "openclawVersion",
    "build",
    "model",
    "providerAuth",
    "hostLabel",
    "osKernel",
    "shell",
    "node",
    "reasoning",
    "elevation",
]

DEFAULT_STATE_FILE = "state/runtime/ygg-self.json"


def _run_capture(command: list[str]) -> str | None:
    try:
        proc = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    text = (proc.stdout or proc.stderr or "").strip()
    return text or None


def detect_timezone_name() -> str:
    tz_env = os.environ.get("TZ")
    if tz_env:
        return tz_env

    localtime = Path("/etc/localtime")
    try:
        if localtime.exists() and localtime.is_symlink():
            resolved = localtime.resolve()
            parts = resolved.parts
            if "zoneinfo" in parts:
                idx = parts.index("zoneinfo")
                return "/".join(parts[idx + 1 :])
    except OSError:
        pass

    timezone_file = Path("/etc/timezone")
    if timezone_file.exists():
        text = timezone_file.read_text(encoding="utf-8").strip()
        if text:
            return text

    return datetime.now().astimezone().tzname() or "unknown"


def detect_host_label() -> str:
    return os.environ.get("OPENCLAW_HOST_LABEL") or os.environ.get("HOSTNAME") or socket.gethostname()


def detect_shell() -> str | None:
    value = os.environ.get("SHELL")
    if not value:
        return None
    return Path(value).name or value


def detect_node_version() -> str | None:
    return _run_capture(["node", "--version"])


def detect_openclaw_version_build() -> tuple[str | None, str | None]:
    text = _run_capture(["openclaw", "--version"])
    if not text:
        return None, None
    match = re.search(r"(\d{4}\.\d+\.\d+)\s*\(([0-9a-f]+)\)", text)
    if match:
        return match.group(1), match.group(2)
    version_match = re.search(r"(\d{4}\.\d+\.\d+)", text)
    if version_match:
        return version_match.group(1), None
    return text, None


def detect_os_kernel() -> str:
    system = platform.system() or "Unknown"
    release = platform.release() or "unknown"
    machine = platform.machine() or "unknown"
    return f"{system} {release} ({machine})"


def compute_fingerprint(snapshot: dict[str, Any]) -> str:
    payload = {field: snapshot.get(field) for field in MEANINGFUL_FIELDS}
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def summarize_changes(old: dict[str, Any], new: dict[str, Any]) -> list[tuple[str, Any, Any]]:
    changes: list[tuple[str, Any, Any]] = []
    for field in MEANINGFUL_FIELDS:
        old_value = old.get(field)
        new_value = new.get(field)
        if old_value != new_value:
            changes.append((field, old_value, new_value))
    return changes


def build_runtime_snapshot(previous: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    openclaw_version, openclaw_build = detect_openclaw_version_build()

    detected: dict[str, Any] = {
        "capturedAt": now_iso_local(),
        "timezone": detect_timezone_name(),
        "channel": os.environ.get("OPENCLAW_CHANNEL"),
        "chatType": os.environ.get("OPENCLAW_CHAT_TYPE"),
        "runtimeCore": os.environ.get("OPENCLAW_RUNTIME_CORE"),
        "sessionKey": os.environ.get("OPENCLAW_SESSION_KEY"),
        "openclawVersion": openclaw_version,
        "build": openclaw_build,
        "model": os.environ.get("OPENCLAW_MODEL"),
        "providerAuth": os.environ.get("OPENCLAW_PROVIDER_AUTH"),
        "hostLabel": detect_host_label(),
        "osKernel": detect_os_kernel(),
        "shell": detect_shell(),
        "node": detect_node_version(),
        "reasoning": os.environ.get("OPENCLAW_REASONING"),
        "elevation": os.environ.get("OPENCLAW_ELEVATION"),
        "notes": previous.get("notes")
        or [
            "Runtime details are a snapshot, not identity.",
            "Preferred design baseline remains Linux VM / Arch-first even if current embodiment varies.",
        ],
    }

    snapshot: dict[str, Any] = {}
    all_keys = set(previous) | set(detected) | set(overrides)
    for key in all_keys:
        if key == "capturedAt":
            snapshot[key] = detected["capturedAt"]
            continue
        if key in overrides and overrides[key] is not None:
            snapshot[key] = overrides[key]
        elif detected.get(key) is not None:
            snapshot[key] = detected[key]
        elif key in previous:
            snapshot[key] = previous[key]

    snapshot["capturedAt"] = detected["capturedAt"]
    snapshot["fingerprint"] = compute_fingerprint(snapshot)
    return snapshot


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: dict[str, Any]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def append_daily_runtime_note(
    daily_dir: Path,
    *,
    changes: list[tuple[str, Any, Any]],
    snapshot: dict[str, Any],
) -> Path:
    bullet_lines: list[str] = []
    for field, old, new in changes:
        old_s = "(unset)" if old in (None, "") else str(old)
        new_s = "(unset)" if new in (None, "") else str(new)
        bullet_lines.append(f"{field}: {old_s} -> {new_s}")
    bullet_lines.append(f"baseline: {snapshot.get('hostLabel', '(unknown)')} / {snapshot.get('osKernel', '(unknown)')}")
    bullet_lines.append(f"fingerprint: {snapshot.get('fingerprint', '(none)')}")
    return append_daily_block(
        daily_dir,
        heading="Heimdall refresh",
        bullet_lines=bullet_lines,
    )


def build_ratatoskr_event(changes: list[tuple[str, Any, Any]], snapshot: dict[str, Any]) -> dict[str, Any]:
    important_fields = {"openclawVersion", "build", "model", "providerAuth", "hostLabel", "sessionKey"}
    importance = "important" if any(field in important_fields for field, _, _ in changes) else "routine"
    return {
        "kind": "runtime-refresh",
        "source": "heimdall",
        "summary": "Runtime embodiment changed",
        "importance": importance,
        "details": {
            "changes": [{"field": field, "old": old, "new": new} for field, old, new in changes],
            "fingerprint": snapshot.get("fingerprint"),
            "sessionKey": snapshot.get("sessionKey"),
            "hostLabel": snapshot.get("hostLabel"),
            "capturedAt": snapshot.get("capturedAt"),
        },
        "route": {
            "daily": True,
            "promote": False,
            "notify": False,
        },
    }


def format_summary(changes: list[tuple[str, Any, Any]], snapshot: dict[str, Any]) -> str:
    if not changes:
        return (
            "Heimdall: no meaningful runtime changes\n"
            f"- fingerprint: {snapshot.get('fingerprint', '(none)')}\n"
            f"- capturedAt: {snapshot.get('capturedAt', '(unknown)')}"
        )

    lines = ["Heimdall: runtime updated"]
    for field, old, new in changes:
        old_s = "(unset)" if old in (None, "") else str(old)
        new_s = "(unset)" if new in (None, "") else str(new)
        lines.append(f"- {field}: {old_s} -> {new_s}")
    lines.append(f"- fingerprint: {snapshot.get('fingerprint', '(none)')}")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Heimdall runtime refresh for Ygg embodiment state.")
    parser.add_argument(
        "--workspace",
        default=str(Path(__file__).resolve().parents[2]),
        help="Workspace root (defaults to the Ygg repo root).",
    )
    parser.add_argument(
        "--state-file",
        default=DEFAULT_STATE_FILE,
        help="Path to Ygg state JSON relative to workspace unless absolute.",
    )
    parser.add_argument(
        "--daily-dir",
        default=DEFAULT_DAILY_DIR,
        help="Daily note directory relative to workspace unless absolute.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Compute without writing state.")
    parser.add_argument("--note", action="store_true", help="Append a runtime note when meaningful fields changed.")
    parser.add_argument("--show-json", action="store_true", help="Print resulting JSON snapshot.")
    parser.add_argument(
        "--ratatoskr",
        action="store_true",
        help="Hand off meaningful runtime changes to Ratatoskr instead of writing Heimdall's direct note.",
    )

    parser.add_argument("--timezone")
    parser.add_argument("--channel")
    parser.add_argument("--chat-type", dest="chatType")
    parser.add_argument("--runtime-core", dest="runtimeCore")
    parser.add_argument("--session-key", dest="sessionKey")
    parser.add_argument("--openclaw-version", dest="openclawVersion")
    parser.add_argument("--build")
    parser.add_argument("--model")
    parser.add_argument("--provider-auth", dest="providerAuth")
    parser.add_argument("--host-label", dest="hostLabel")
    parser.add_argument("--os-kernel", dest="osKernel")
    parser.add_argument("--shell")
    parser.add_argument("--node")
    parser.add_argument("--reasoning")
    parser.add_argument("--elevation")
    return parser.parse_args(argv)


def resolve_under_workspace(workspace: Path, raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    return workspace / path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    workspace = Path(args.workspace).resolve()
    state_path = resolve_under_workspace(workspace, args.state_file)
    daily_dir = resolve_under_workspace(workspace, args.daily_dir)

    state = load_state(state_path)
    previous_snapshot = state.get("runtimeSnapshot", {})
    overrides = {
        key: value
        for key, value in vars(args).items()
        if key
        in {
            "timezone",
            "channel",
            "chatType",
            "runtimeCore",
            "sessionKey",
            "openclawVersion",
            "build",
            "model",
            "providerAuth",
            "hostLabel",
            "osKernel",
            "shell",
            "node",
            "reasoning",
            "elevation",
        }
        and value is not None
    }

    snapshot = build_runtime_snapshot(previous_snapshot, overrides)
    changes = summarize_changes(previous_snapshot, snapshot)

    history = dict(state.get("runtimeHistory", {}))
    history["lastRefreshAt"] = snapshot["capturedAt"]
    history["lastFingerprint"] = snapshot["fingerprint"]
    if changes:
        history["lastMeaningfulChangeAt"] = snapshot["capturedAt"]

    state["runtimeSnapshot"] = snapshot
    state["runtimeHistory"] = history

    if not args.dry_run:
        save_state(state_path, state)
        if args.note and changes:
            if args.ratatoskr:
                event = build_ratatoskr_event(changes, snapshot)
                route_event(workspace, event, daily_dir=args.daily_dir)
            else:
                append_daily_runtime_note(daily_dir, changes=changes, snapshot=snapshot)

    if args.show_json:
        print(json.dumps(snapshot, indent=2))
    else:
        print(format_summary(changes, snapshot))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
