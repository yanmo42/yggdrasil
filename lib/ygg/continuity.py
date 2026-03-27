from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ALLOWED_DISPOSITIONS = {
    "DROP_LOCAL",
    "LOG_ONLY",
    "TODO_PROMOTE",
    "DOC_PROMOTE",
    "POLICY_PROMOTE",
    "ESCALATE",
}

PROMOTION_DISPOSITIONS = {
    "TODO_PROMOTE",
    "DOC_PROMOTE",
    "POLICY_PROMOTE",
    "ESCALATE",
}


@dataclass(frozen=True)
class ContinuityCheckpoint:
    timestamp: str
    lane: str
    summary: str
    disposition: str
    promotion_target: str = ""
    evidence: str = ""
    next_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContinuityCheckpoint":
        return cls(
            timestamp=str(data["timestamp"]),
            lane=str(data["lane"]),
            summary=str(data["summary"]),
            disposition=str(data["disposition"]),
            promotion_target=str(data.get("promotion_target", "")),
            evidence=str(data.get("evidence", "")),
            next_action=str(data.get("next_action", "")),
        )


def checkpoint_dir(root: str | Path) -> Path:
    return Path(root) / "state" / "ygg" / "checkpoints"


def write_checkpoint(
    root: str | Path,
    *,
    lane: str,
    summary: str,
    disposition: str,
    promotion_target: str = "",
    evidence: str = "",
    next_action: str = "",
) -> Path:
    lane = str(lane or "").strip()
    summary = str(summary or "").strip()
    promotion_target = str(promotion_target or "").strip()
    evidence = str(evidence or "").strip()
    next_action = str(next_action or "").strip()

    if disposition not in ALLOWED_DISPOSITIONS:
        raise ValueError(f"Invalid disposition: {disposition}")
    if not lane:
        raise ValueError("lane must be non-empty")
    if not summary:
        raise ValueError("summary must be non-empty")
    if disposition in PROMOTION_DISPOSITIONS and not promotion_target:
        raise ValueError(f"promotion_target is required for disposition {disposition}")

    checkpoint = ContinuityCheckpoint(
        timestamp=datetime.now(UTC).isoformat(),
        lane=lane,
        summary=summary,
        disposition=disposition,
        promotion_target=promotion_target,
        evidence=evidence,
        next_action=next_action,
    )

    out_dir = checkpoint_dir(root)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = checkpoint.timestamp.replace(":", "-")
    out_path = out_dir / f"{stamp}_{lane.replace(' ', '_')}.json"
    out_path.write_text(json.dumps(checkpoint.to_dict(), indent=2) + "\n", encoding="utf-8")
    return out_path


def load_latest_checkpoint(root: str | Path) -> ContinuityCheckpoint | None:
    directory = checkpoint_dir(root)
    if not directory.exists():
        return None

    candidates = sorted(directory.glob("*.json"))
    if not candidates:
        return None

    data = json.loads(candidates[-1].read_text(encoding="utf-8"))
    return ContinuityCheckpoint.from_dict(data)
