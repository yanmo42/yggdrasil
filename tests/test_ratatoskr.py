from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from ygg.ratatoskr import build_daily_bullets, route_event


class RatatoskrTests(unittest.TestCase):
    def test_route_event_writes_daily_and_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            event = {
                "kind": "runtime-refresh",
                "source": "heimdall",
                "summary": "Runtime embodiment changed after restart",
                "importance": "important",
                "details": {
                    "changes": [
                        {"field": "openclawVersion", "old": "2026.4.0", "new": "2026.4.1"}
                    ],
                    "fingerprint": "abc123",
                },
                "route": {
                    "daily": True,
                    "promote": True,
                    "notify": False,
                },
            }

            with patch("ygg.runtime_notes.today_local", return_value="2026-04-02"), patch(
                "ygg.runtime_notes.time_local_hm", return_value="10:45"
            ):
                result = route_event(root, event)
                daily_text = (root / "state/notes/daily/2026-04-02.md").read_text(encoding="utf-8")
                promo_lines = [
                    json.loads(line)
                    for line in (root / "state/runtime/promotion-candidates.jsonl").read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]

            self.assertIn("Ratatoskr - runtime-refresh", daily_text)
            self.assertIn("change openclawVersion: 2026.4.0 -> 2026.4.1", daily_text)
            self.assertEqual("Runtime embodiment changed after restart", promo_lines[0]["summary"])
            self.assertEqual("runtime-refresh", promo_lines[0]["eventKind"])
            self.assertIsNotNone(result["daily"])
            self.assertIsNotNone(result["promotion"])

    def test_route_event_dedupes_promotion_candidates_by_event_id(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            event = {
                "id": "evt_123",
                "kind": "continuity.note",
                "source": "kernel-bootstrap",
                "summary": "Kernel milestone worth review",
                "importance": "important",
                "details": {"files": ["docs/CONTINUITY-OPS-V1.md"]},
                "route": {"daily": False, "promote": True, "notify": False},
            }
            route_event(root, event)
            route_event(root, event)
            promo_lines = [
                json.loads(line)
                for line in (root / "state/runtime/promotion-candidates.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

            self.assertEqual(1, len(promo_lines))
            self.assertEqual("promo:evt_123", promo_lines[0]["id"])
            self.assertEqual("evt_123", promo_lines[0]["sourceEventId"])

    def test_build_daily_bullets_flattens_changes_and_details(self) -> None:
        event = {
            "kind": "runtime-refresh",
            "source": "heimdall",
            "summary": "Runtime embodiment changed",
            "importance": "routine",
            "details": {
                "changes": [
                    {"field": "model", "old": "old-model", "new": "new-model"}
                ],
                "fingerprint": "ff00aa",
                "sessionKey": "agent:claw:main",
            },
            "route": {"daily": True},
        }
        bullets = build_daily_bullets(event)
        rendered = "\n".join(bullets)
        self.assertIn("summary: Runtime embodiment changed", rendered)
        self.assertIn("change model: old-model -> new-model", rendered)
        self.assertIn("fingerprint: ff00aa", rendered)
        self.assertIn("sessionKey: agent:claw:main", rendered)


if __name__ == "__main__":
    unittest.main()
