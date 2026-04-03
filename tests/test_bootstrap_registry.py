import os
import sys
import unittest
from pathlib import Path

REPO_LIB = Path(__file__).resolve().parents[1] / "lib"
sys.path.insert(0, str(REPO_LIB))

existing_ygg = sys.modules.get("ygg")
existing_file = getattr(existing_ygg, "__file__", "") if existing_ygg is not None else ""
if existing_ygg is not None and not str(existing_file).startswith(str(REPO_LIB)):
    sys.modules.pop("ygg", None)

from ygg.bootstrap_registry import render_shell_assignments
from ygg.bootstrap_registry import render_path_contract


REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY = REPO_ROOT / "state" / "profiles" / "components.yaml"


class TestBootstrapRegistry(unittest.TestCase):
    def test_stable_profile_renders_expected_defaults(self) -> None:
        rendered = render_shell_assignments(REGISTRY, profile="stable", env={})
        self.assertIn("WORKSPACE_ROOT=", rendered)
        self.assertIn("YGG_ROOT=", rendered)
        self.assertIn("TARA_ROOT=", rendered)
        self.assertIn("ENABLE_SPINE=1", rendered)
        self.assertIn("ENABLE_YGG=1", rendered)
        self.assertIn("ENABLE_TARA=1", rendered)
        self.assertIn("ENABLE_SANDY_CHAOS=0", rendered)
        self.assertIn("ENABLE_IANMOOG_SITE=0", rendered)

    def test_env_overrides_win_over_registry_defaults(self) -> None:
        env = {
            "YGG_GIT_URL": "git@github.com:example/ygg.git",
            "ENABLE_SANDY_CHAOS": "1",
            "SANDY_ROOT": "/tmp/sandy-chaos",
        }
        rendered = render_shell_assignments(REGISTRY, profile="stable", env=env)
        self.assertIn("YGG_GIT_URL=git@github.com:example/ygg.git", rendered)
        self.assertIn("ENABLE_SANDY_CHAOS=1", rendered)
        self.assertIn("SANDY_ROOT=/tmp/sandy-chaos", rendered)

    def test_render_path_contract_uses_registry_for_paths(self) -> None:
        contract = render_path_contract(
            REGISTRY,
            profile="stable",
            contract_path="/tmp/ygg-paths.yaml",
            env={"PROJECTS_ROOT": "/tmp/projects"},
        )
        self.assertIn("profile: stable", contract)
        self.assertIn("root: /home/ian/.openclaw/workspace-claw-main", contract)
        self.assertIn("root: /tmp/projects", contract)
        self.assertIn("tara: /home/ian/tara", contract)
        self.assertIn("sandy-chaos: /tmp/projects/sandy-chaos", contract)
        self.assertIn("canonical_path_registry: /tmp/ygg-paths.yaml", contract)


if __name__ == "__main__":
    unittest.main()
