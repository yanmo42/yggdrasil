import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = REPO_ROOT / "machine" / "bootstrap-host.sh"


class TestBootstrapProfiles(unittest.TestCase):
    def _run(self, profile: str) -> str:
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            env = os.environ.copy()
            env["HOME"] = str(home)
            proc = subprocess.run(
                [str(BOOTSTRAP), "--dry-run", "--skip-openclaw-install", "--profile", profile],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
        return proc.stdout

    def test_stable_profile_uses_stable_manifests_and_disables_optional_repos(self) -> None:
        output = self._run("stable")
        self.assertIn("profile:   stable", output)
        self.assertIn("arch-packages.base.txt", output)
        self.assertIn("arch-packages.stable.txt", output)
        self.assertIn("skip sandy-chaos (disabled in profile)", output)
        self.assertIn("skip ianmoog-site (disabled in profile)", output)

    def test_dev_profile_uses_dev_manifests_and_enables_optional_repos(self) -> None:
        output = self._run("dev")
        self.assertIn("profile:   dev", output)
        self.assertIn("arch-packages.base.txt", output)
        self.assertIn("arch-packages.dev.txt", output)
        self.assertIn("skip sandy-chaos (no git URL provided)", output)
        self.assertIn("skip ianmoog-site (no git URL provided)", output)

    def test_bootstrap_writes_and_checks_the_override_contract(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            workspace = home / "custom-ws"
            projects = home / "custom-projects"
            ygg_root = REPO_ROOT
            tara_root = home / "tara"
            (workspace / "scripts").mkdir(parents=True, exist_ok=True)
            (workspace / "scripts" / "work.py").write_text("print('work')\n", encoding="utf-8")
            (workspace / "scripts" / "resume.py").write_text("print('resume')\n", encoding="utf-8")
            tara_root.mkdir(parents=True, exist_ok=True)

            env = os.environ.copy()
            env["HOME"] = str(home)
            env["ENABLE_SPINE"] = "0"
            env["ENABLE_YGG"] = "0"
            env["ENABLE_TARA"] = "0"
            env["ENABLE_SANDY_CHAOS"] = "0"
            env["ENABLE_IANMOOG_SITE"] = "0"

            proc = subprocess.run(
                [
                    str(BOOTSTRAP),
                    "--skip-install",
                    "--skip-openclaw-install",
                    "--rewrite-path-contract",
                    "--profile",
                    "stable",
                    "--workspace-root",
                    str(workspace),
                    "--projects-root",
                    str(projects),
                    "--ygg-root",
                    str(ygg_root),
                    "--tara-root",
                    str(tara_root),
                ],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )

            contract = (workspace / "config" / "ygg-paths.yaml").read_text(encoding="utf-8")
            self.assertIn(f"root: {workspace}", contract)
            self.assertIn(f"root: {projects}", contract)
            self.assertIn(f"canonical_path_registry: {workspace / 'config' / 'ygg-paths.yaml'}", contract)
            self.assertIn(f"contract path: {workspace / 'config' / 'ygg-paths.yaml'}", proc.stdout)
            self.assertIn(f"- spine root: {workspace}", proc.stdout)
            self.assertIn(f"- work repos root: {projects}", proc.stdout)


if __name__ == "__main__":
    unittest.main()
