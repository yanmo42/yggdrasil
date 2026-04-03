from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from ygg.heimdall import (
    append_daily_runtime_note,
    build_kernel_runtime_events,
    build_ratatoskr_event,
    main,
)


class HeimdallTests(unittest.TestCase):
    def test_build_kernel_runtime_events_emits_refresh_and_changed(self) -> None:
        changes = [("openclawVersion", "2026.4.0", "2026.4.1"), ("model", "old", "new")]
        snapshot = {
            "fingerprint": "abc123",
            "sessionKey": "agent:claw:main",
            "hostLabel": "not-ur-pc-pal",
            "capturedAt": "2026-04-02T10:45:00-04:00",
            "channel": "webchat",
            "model": "new",
        }
        events = build_kernel_runtime_events(changes, snapshot)
        self.assertEqual(2, len(events))
        self.assertEqual("runtime.refresh", events[0]["kind"])
        self.assertEqual("runtime.changed", events[1]["kind"])
        self.assertEqual("important", events[1]["importance"])
        self.assertEqual("agent:claw:main", events[1]["links"]["sessionKey"])
        self.assertTrue(events[1]["route"]["daily"])

    def test_build_ratatoskr_event_marks_important_runtime_changes(self) -> None:
        changes = [("openclawVersion", "2026.4.0", "2026.4.1"), ("model", "old", "new")]
        snapshot = {
            "fingerprint": "abc123",
            "sessionKey": "agent:claw:main",
            "hostLabel": "not-ur-pc-pal",
            "capturedAt": "2026-04-02T10:45:00-04:00",
        }
        event = build_ratatoskr_event(changes, snapshot)
        self.assertEqual("runtime-refresh", event["kind"])
        self.assertEqual("heimdall", event["source"])
        self.assertEqual("important", event["importance"])
        self.assertTrue(event["route"]["daily"])
        self.assertFalse(event["route"]["promote"])

    def test_main_updates_runtime_and_history(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            state_path = root / "state" / "runtime" / "ygg-self.json"
            kernel_path = root / "state" / "runtime" / "ygg-kernel.json"
            event_queue_path = root / "state" / "runtime" / "event-queue.jsonl"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
                json.dumps(
                    {
                        "runtimeSnapshot": {
                            "capturedAt": "2026-04-02T09:38:00-04:00",
                            "timezone": "America/New_York",
                            "hostLabel": "old-host",
                            "openclawVersion": "2026.4.0",
                            "build": "abc1234",
                            "osKernel": "Linux old (x64)",
                            "shell": "zsh",
                            "node": "v25.8.0",
                            "fingerprint": "oldfingerprint",
                        }
                    }
                ),
                encoding="utf-8",
            )
            kernel_path.write_text(
                json.dumps(
                    {
                        "schemaVersion": "0.1.0",
                        "bootState": {
                            "initializedAt": "2026-04-02T09:00:00-04:00",
                            "lastReviewedAt": "2026-04-02T09:00:00-04:00",
                            "lastWakeSummary": None,
                            "lastEventId": None,
                            "lastPromotionId": None,
                        },
                    }
                ),
                encoding="utf-8",
            )

            with patch(
                "ygg.heimdall.detect_timezone_name",
                return_value="America/New_York",
            ), patch(
                "ygg.heimdall.detect_host_label",
                return_value="new-host",
            ), patch(
                "ygg.heimdall.detect_openclaw_version_build",
                return_value=("2026.4.1", "da64a97"),
            ), patch(
                "ygg.heimdall.detect_os_kernel",
                return_value="Linux 6.6.87.2-microsoft-standard-WSL2 (x64)",
            ), patch(
                "ygg.heimdall.detect_shell",
                return_value="zsh",
            ), patch(
                "ygg.heimdall.detect_node_version",
                return_value="v25.8.1",
            ), patch(
                "ygg.heimdall.now_iso_local",
                return_value="2026-04-02T10:15:00-04:00",
            ):
                rc = main(
                    [
                        "--workspace",
                        str(root),
                        "--model",
                        "openai-codex/gpt-5.4",
                        "--session-key",
                        "agent:claw:main",
                        "--channel",
                        "webchat",
                        "--chat-type",
                        "direct",
                        "--runtime-core",
                        "claw-main",
                        "--reasoning",
                        "off",
                        "--elevation",
                        "enabled",
                    ]
                )

            self.assertEqual(0, rc)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            snapshot = state["runtimeSnapshot"]
            history = state["runtimeHistory"]
            queued_events = [
                json.loads(line)
                for line in event_queue_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            kernel_state = json.loads(kernel_path.read_text(encoding="utf-8"))
            self.assertEqual("new-host", snapshot["hostLabel"])
            self.assertEqual("2026.4.1", snapshot["openclawVersion"])
            self.assertEqual("da64a97", snapshot["build"])
            self.assertEqual("openai-codex/gpt-5.4", snapshot["model"])
            self.assertEqual("2026-04-02T10:15:00-04:00", history["lastRefreshAt"])
            self.assertEqual("2026-04-02T10:15:00-04:00", history["lastMeaningfulChangeAt"])
            self.assertTrue(snapshot["fingerprint"])
            self.assertEqual(2, len(queued_events))
            self.assertEqual("runtime.refresh", queued_events[0]["kind"])
            self.assertEqual("runtime.changed", queued_events[1]["kind"])
            self.assertEqual(
                queued_events[-1]["id"],
                kernel_state["bootState"]["lastEventId"],
            )

    def test_append_daily_runtime_note_dedupes_trailing_block(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            daily_dir = Path(td)
            snapshot = {
                "hostLabel": "not-ur-pc-pal",
                "osKernel": "Linux 6.6.87.2-microsoft-standard-WSL2 (x64)",
                "fingerprint": "1234abcd",
            }
            changes = [("model", "old-model", "new-model")]
            with patch(
                "ygg.runtime_notes.today_local",
                return_value="2026-04-02",
            ), patch(
                "ygg.runtime_notes.time_local_hm",
                return_value="10:20",
            ):
                first = append_daily_runtime_note(
                    daily_dir,
                    changes=changes,
                    snapshot=snapshot,
                )
                second = append_daily_runtime_note(
                    daily_dir,
                    changes=changes,
                    snapshot=snapshot,
                )

            self.assertEqual(first, second)
            text = first.read_text(encoding="utf-8")
            self.assertEqual(1, text.count("## 10:20 Heimdall refresh"))


if __name__ == "__main__":
    unittest.main()
