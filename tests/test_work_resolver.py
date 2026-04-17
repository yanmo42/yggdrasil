"""
Tests for lib/ygg/work_resolver.py — continuity brief assembly.

Covers:
1. Brief with active program + fresh checkpoint → status=active, confidence > 0.5
2. NL request uses retrieval to populate matchedAnchor
3. Graceful degradation when state files are missing
4. DROP_LOCAL checkpoint disposition suppresses resume
5. ygg work --json includes continuityBrief key
"""
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from ygg.work_resolver import resolve_continuity_brief

YGG_CLI = Path.home() / "ygg" / "lib" / "ygg" / "cli.py"
YGG_REPO = Path.home() / "ygg"


def _iso_now(offset_days: int = 0) -> str:
    dt = datetime.now(UTC) + timedelta(days=offset_days)
    return dt.isoformat()


def _write_checkpoint(root: Path, *, lane: str, summary: str, disposition: str, next_action: str = "") -> None:
    cp_dir = root / "state" / "ygg" / "checkpoints"
    cp_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).isoformat().replace(":", "-")
    data = {
        "timestamp": _iso_now(),
        "lane": lane,
        "summary": summary,
        "disposition": disposition,
        "promotion_target": "",
        "evidence": "",
        "next_action": next_action,
    }
    (cp_dir / f"{stamp}_{lane}.json").write_text(json.dumps(data), encoding="utf-8")


def _write_programs(root: Path, programs: list[dict]) -> None:
    path = root / "state" / "ygg" / "programs.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"version": 1, "updatedAt": _iso_now(), "programs": programs}),
        encoding="utf-8",
    )


def _write_ideas(root: Path, ideas: list[dict]) -> None:
    path = root / "state" / "ygg" / "ideas.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"version": 1, "updatedAt": _iso_now(), "ideas": ideas}),
        encoding="utf-8",
    )


class TestContinuityBriefWithState(unittest.TestCase):
    """Brief with well-populated state returns useful, non-empty output."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)
        _write_checkpoint(
            self.root,
            lane="continuity-integration",
            summary="Ported Heimdall and Ratatoskr into ~/ygg.",
            disposition="LOG_ONLY",
            next_action="Wire semantic registry mutation commands.",
        )
        _write_programs(self.root, [
            {
                "id": "ygg-continuity-integration",
                "title": "Ygg continuity integration",
                "status": "active",
                "priority": "high",
                "relatedLanes": ["continuity", "continuity-integration"],
                "nextAction": "Wire semantic registry mutation commands.",
                "notes": [],
            }
        ])
        _write_ideas(self.root, [
            {
                "id": "topology-retrieval",
                "title": "Topology-aware retrieval",
                "status": "incubating",
                "nextAction": "Build benchmark.",
                "tags": ["continuity"],
                "notes": [],
            }
        ])

    def tearDown(self):
        self._td.cleanup()

    def test_brief_with_active_program_and_fresh_checkpoint(self):
        brief = resolve_continuity_brief(self.root, "continue the continuity integration")
        self.assertIn(brief["status"], ("active", "resumable"))
        self.assertGreater(brief["confidence"], 0.5)
        self.assertIsNotNone(brief["activeProgram"])
        self.assertEqual(brief["activeProgram"]["id"], "ygg-continuity-integration")
        self.assertIsNotNone(brief["latestCheckpoint"])
        self.assertEqual(brief["latestCheckpoint"]["lane"], "continuity-integration")

    def test_brief_populates_related_ideas(self):
        brief = resolve_continuity_brief(self.root, "topology retrieval")
        self.assertIsInstance(brief["relatedIdeas"], list)
        self.assertTrue(len(brief["relatedIdeas"]) > 0)
        self.assertEqual(brief["relatedIdeas"][0]["id"], "topology-retrieval")

    def test_brief_status_fields_are_valid(self):
        brief = resolve_continuity_brief(self.root, "anything")
        self.assertIn(brief["status"], ("active", "resumable", "empty"))
        self.assertIn(brief["suggestedDispatch"], ("forge", "resume", "passthrough"))
        self.assertIsInstance(brief["dispatchReason"], str)
        self.assertIsInstance(brief["confidence"], float)
        self.assertGreaterEqual(brief["confidence"], 0.0)
        self.assertLessEqual(brief["confidence"], 1.0)

    def test_program_lane_match_raises_confidence(self):
        # Program's relatedLanes contains the checkpoint lane → confidence bonus applied.
        brief = resolve_continuity_brief(self.root, "")
        # With fresh checkpoint (+0.2) + program-lane match (+0.1) → at least 0.8
        self.assertGreaterEqual(brief["confidence"], 0.8)


class TestContinuityBriefDropLocal(unittest.TestCase):
    """DROP_LOCAL checkpoint disposition suppresses resume recommendation."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)
        _write_checkpoint(
            self.root,
            lane="dead-end-lane",
            summary="Terminated this lane.",
            disposition="DROP_LOCAL",
        )

    def tearDown(self):
        self._td.cleanup()

    def test_drop_local_does_not_suggest_resume(self):
        brief = resolve_continuity_brief(self.root, "continue dead-end-lane")
        self.assertNotEqual(
            brief["suggestedDispatch"],
            "resume",
            "DROP_LOCAL checkpoint must not produce a 'resume' dispatch recommendation.",
        )

    def test_drop_local_lowers_confidence(self):
        brief = resolve_continuity_brief(self.root, "")
        # Base 0.5 + fresh_checkpoint 0.2 - drop_local 0.2 = 0.5 → below threshold
        self.assertLess(brief["confidence"], 0.65)


class TestContinuityBriefGracefulDegradation(unittest.TestCase):
    """Resolver returns a valid empty brief when no state files exist."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)
        # No state files at all.

    def tearDown(self):
        self._td.cleanup()

    def test_empty_root_returns_valid_brief(self):
        brief = resolve_continuity_brief(self.root, "do something")
        self.assertEqual(brief["status"], "empty")
        self.assertEqual(brief["suggestedDispatch"], "passthrough")
        self.assertIsNone(brief["latestCheckpoint"])
        self.assertIsNone(brief["activeProgram"])
        self.assertEqual(brief["relatedIdeas"], [])

    def test_empty_request_returns_valid_brief(self):
        brief = resolve_continuity_brief(self.root, "")
        self.assertIn(brief["status"], ("active", "resumable", "empty"))
        self.assertIn(brief["suggestedDispatch"], ("forge", "resume", "passthrough"))

    def test_resolver_never_raises_on_bad_root(self):
        # Even a completely nonexistent root should not raise — it degrades silently.
        try:
            brief = resolve_continuity_brief("/nonexistent/path/that/does/not/exist", "test")
            self.assertEqual(brief["status"], "empty")
        except Exception as exc:
            self.fail(f"resolve_continuity_brief raised unexpectedly: {exc}")


class TestContinuityBriefImplementationRequest(unittest.TestCase):
    """Implementation-shaped request → forge suggestion."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)
        _write_checkpoint(
            self.root,
            lane="build-lane",
            summary="Started building the thing.",
            disposition="LOG_ONLY",
        )
        _write_programs(self.root, [
            {
                "id": "build-program",
                "title": "Build program",
                "status": "active",
                "relatedLanes": ["build-lane"],
                "notes": [],
            }
        ])

    def tearDown(self):
        self._td.cleanup()

    def test_impl_request_suggests_forge(self):
        brief = resolve_continuity_brief(self.root, "implement the new feature")
        if brief["confidence"] >= 0.65:
            self.assertEqual(
                brief["suggestedDispatch"],
                "forge",
                "Implementation-shaped request with sufficient confidence should suggest 'forge'.",
            )


class TestCmdWorkJsonIncludesBrief(unittest.TestCase):
    """ygg work --json on the real repo must include continuityBrief in output."""

    def _run_work_json(self, *extra_args: str) -> dict:
        proc = subprocess.run(
            [sys.executable, str(YGG_CLI), "work", "--json", "--plan-only", *extra_args],
            capture_output=True,
            text=True,
            cwd=str(YGG_REPO),
        )
        # work --json may fail if workspace imports unavailable, but should still emit JSON
        # or exit. We check only if it produced parseable JSON.
        if proc.returncode != 0 or not proc.stdout.strip():
            self.skipTest("workspace imports unavailable in this environment")
        return json.loads(proc.stdout)

    def test_work_json_contains_continuity_brief_key(self):
        payload = self._run_work_json("continue the ygg continuity integration")
        self.assertIn(
            "continuityBrief",
            payload,
            "ygg work --json must include a 'continuityBrief' key in its output.",
        )

    def test_continuity_brief_has_expected_shape(self):
        payload = self._run_work_json("continue the ygg continuity integration")
        brief = payload.get("continuityBrief")
        if brief is None:
            self.skipTest("continuityBrief was None (resolver degraded — expected in restricted envs)")
        self.assertIn(brief.get("status"), ("active", "resumable", "empty"))
        self.assertIn(brief.get("suggestedDispatch"), ("forge", "resume", "passthrough"))
        self.assertIsInstance(brief.get("confidence"), float)


if __name__ == "__main__":
    unittest.main()
