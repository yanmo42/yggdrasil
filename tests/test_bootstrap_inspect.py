import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


YGG_CLI = Path.home() / "ygg" / "lib" / "ygg" / "cli.py"


class TestBootstrapInspect(unittest.TestCase):
    def test_bootstrap_inspect_json_contains_profile_components_and_path_preview(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(YGG_CLI), "bootstrap", "inspect", "--profile", "stable", "--json"],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["profile"]["name"], "stable")
        self.assertIn("components.yaml", payload["registry"]["path"])
        self.assertTrue(payload["components"])
        component_ids = {row["id"] for row in payload["components"]}
        self.assertIn("ygg", component_ids)
        self.assertIn("tara", component_ids)
        self.assertIn("schema: ygg-paths/v1", payload["path_contract_preview"])

    def test_bootstrap_inspect_uses_env_overrides_for_assignments_and_preview(self) -> None:
        env = os.environ.copy()
        env["PROJECTS_ROOT"] = "/tmp/custom-projects"
        env["WORKSPACE_ROOT"] = "/tmp/custom-ws"
        proc = subprocess.run(
            [sys.executable, str(YGG_CLI), "bootstrap", "inspect", "--profile", "stable", "--json"],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["assignments"]["PROJECTS_ROOT"], "/tmp/custom-projects")
        self.assertEqual(payload["assignments"]["WORKSPACE_ROOT"], "/tmp/custom-ws")
        self.assertIn("root: /tmp/custom-projects", payload["path_contract_preview"])
        self.assertIn("root: /tmp/custom-ws", payload["path_contract_preview"])
        by_id = {row["id"]: row for row in payload["components"]}
        self.assertEqual(by_id["spine"]["root"], "/tmp/custom-ws")
        self.assertEqual(by_id["sandy-chaos"]["root"], "/tmp/custom-projects/sandy-chaos")


if __name__ == "__main__":
    unittest.main()
