import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

YGG_CLI = Path.home() / "ygg" / "lib" / "ygg" / "cli.py"


class TestRavensV1(unittest.TestCase):
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
                    f"    bin: {ygg_root / 'bin' / 'ygg'}",
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

    def _run(self, home: Path, *args: str) -> dict:
        contract = self._ensure_contract(home)

        env = os.environ.copy()
        env["HOME"] = str(home)
        env["YGG_PATHS_FILE"] = str(contract)
        proc = subprocess.run(
            [sys.executable, str(YGG_CLI), *args],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        if proc.stdout.strip().startswith("{") or proc.stdout.strip().startswith("["):
            return json.loads(proc.stdout)
        return {"text": proc.stdout}

    def test_raven_launch_status_inspect_return_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            payload = self._run(
                home,
                "raven",
                "launch",
                "--trigger",
                "heartbeat",
                "--actors",
                "huginn,muninn",
                "inspect env drift",
                "--json",
            )
            flight_id = payload["id"]
            self.assertTrue(flight_id.startswith("RAVEN-"))

            flights_file = home / "ygg" / "state" / "runtime" / "ravens" / "flights" / f"{flight_id}.json"
            logs_file = home / "ygg" / "state" / "runtime" / "ravens" / "logs" / f"{flight_id}.jsonl"
            self.assertTrue(flights_file.exists())
            self.assertTrue(logs_file.exists())

            status = self._run(home, "raven", "status", "--json")
            self.assertTrue(any(row.get("id") == flight_id for row in status))

            inspected = self._run(home, "raven", "inspect", flight_id, "--json")
            self.assertEqual(inspected["id"], flight_id)
            self.assertEqual(inspected["status"], "launched")

            returned = self._run(
                home,
                "raven",
                "return",
                flight_id,
                "--evidence",
                "file:~/ygg/docs/RAVENS-V1.md",
                "--failure-condition",
                "no evidence linkage",
                "--recommendation",
                "Open a trial graft proposal.",
                "--json",
            )
            self.assertEqual(returned["id"], flight_id)
            return_file = Path(returned["returnFile"])
            self.assertTrue(return_file.exists())

            inspected_after = self._run(home, "raven", "inspect", flight_id, "--json")
            self.assertEqual(inspected_after["status"], "returned")

    def test_graft_and_beak_proposals_create_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            graft = self._run(
                home,
                "graft",
                "propose",
                "Add proposal gate protocol",
                "--target-attachment",
                "state/policy/",
                "--json",
            )
            self.assertTrue(graft["id"].startswith("GRAFT-"))
            self.assertTrue(Path(graft["file"]).exists())

            beak = self._run(
                home,
                "beak",
                "propose",
                "Prune duplicate docs",
                "--target",
                "docs/",
                "--problem-type",
                "duplication",
                "--json",
            )
            self.assertTrue(beak["id"].startswith("BEAK-"))
            self.assertEqual(beak["class"], "soft")
            self.assertTrue(Path(beak["file"]).exists())


if __name__ == "__main__":
    unittest.main()
