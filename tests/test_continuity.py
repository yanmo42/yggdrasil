import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from ygg.continuity import load_latest_checkpoint, write_checkpoint

REPO_ROOT = Path(__file__).resolve().parents[1]
YGG_CLI = REPO_ROOT / "lib" / "ygg" / "cli.py"
BIN_YGG = REPO_ROOT / "bin" / "ygg"


class TestContinuityBridge(unittest.TestCase):
    def _ensure_contract(self, home: Path) -> Path:
        contract = home / "ygg-paths.yaml"
        workspace = home / ".openclaw" / "workspace-claw-main"
        ygg_root = home / "ygg"
        projects = home / "projects"
        workspace.mkdir(parents=True, exist_ok=True)
        ygg_root.mkdir(parents=True, exist_ok=True)
        projects.mkdir(parents=True, exist_ok=True)

        contract.write_text(
            "\n".join(
                [
                    "schema: ygg-paths/v1",
                    "profile: test",
                    "paths:",
                    "  spine:",
                    f"    root: {workspace}",
                    "  control_plane:",
                    "    name: ygg",
                    f"    root: {ygg_root}",
                    f"    bin: {BIN_YGG}",
                    "  work_repos:",
                    f"    root: {projects}",
                    "contracts:",
                    "  canonical_state_owner: spine",
                    f"  canonical_path_registry: {contract}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        return contract

    def _env(self, home: Path) -> dict[str, str]:
        contract = self._ensure_contract(home)
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["YGG_PATHS_FILE"] = str(contract)
        return env

    def _run_cli(self, home: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(YGG_CLI), *args],
            check=True,
            capture_output=True,
            text=True,
            env=self._env(home),
        )

    def test_module_write_and_load_latest_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "ygg"
            path = write_checkpoint(
                root,
                lane="bridge-lane",
                summary="continuity kernel ported",
                disposition="LOG_ONLY",
                evidence="tests",
                next_action="verify cli",
            )

            self.assertTrue(path.exists())
            self.assertEqual(path.parent, root / "state" / "ygg" / "checkpoints")

            latest = load_latest_checkpoint(root)
            self.assertIsNotNone(latest)
            assert latest is not None
            self.assertEqual(latest.lane, "bridge-lane")
            self.assertEqual(latest.summary, "continuity kernel ported")
            self.assertEqual(latest.disposition, "LOG_ONLY")
            self.assertEqual(latest.evidence, "tests")
            self.assertEqual(latest.next_action, "verify cli")

    def test_cli_checkpoint_status_and_promote_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)

            checkpoint = json.loads(
                self._run_cli(
                    home,
                    "checkpoint",
                    "--lane",
                    "sc-ygg-bridge",
                    "--summary",
                    "Initial bridge checkpoint",
                    "--disposition",
                    "LOG_ONLY",
                    "--evidence",
                    "unit-tests",
                    "--next-action",
                    "smoke the wrapper",
                ).stdout
            )
            checkpoint_path = home / "ygg" / checkpoint["checkpoint"]
            self.assertTrue(checkpoint_path.exists())

            status = json.loads(self._run_cli(home, "status", "--continuity").stdout)
            self.assertEqual(status["lane"], "sc-ygg-bridge")
            self.assertEqual(status["disposition"], "LOG_ONLY")
            self.assertEqual(status["evidence"], "unit-tests")

            promoted = json.loads(
                self._run_cli(
                    home,
                    "promote",
                    "--lane",
                    "sc-ygg-bridge",
                    "--summary",
                    "Promote bridge contract",
                    "--disposition",
                    "DOC_PROMOTE",
                    "--promotion-target",
                    "docs/CONTINUITY-OPS-V1.md",
                    "--evidence",
                    "smoke-ok",
                    "--next-action",
                    "land follow-up docs",
                ).stdout
            )
            promoted_path = home / "ygg" / promoted["promotion_checkpoint"]
            self.assertTrue(promoted_path.exists())

            latest = json.loads(self._run_cli(home, "status", "--continuity").stdout)
            self.assertEqual(latest["summary"], "Promote bridge contract")
            self.assertEqual(latest["disposition"], "DOC_PROMOTE")
            self.assertEqual(latest["promotion_target"], "docs/CONTINUITY-OPS-V1.md")

    def test_legacy_promote_dry_run_still_available(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            proc = self._run_cli(
                home,
                "promote",
                "demo-domain",
                "demo-task",
                "--disposition",
                "log-daily",
                "--dry-run",
            )
            self.assertIn("Ygg promote dry-run", proc.stdout)
            self.assertIn('"disposition": "log-daily"', proc.stdout)


if __name__ == "__main__":
    unittest.main()
