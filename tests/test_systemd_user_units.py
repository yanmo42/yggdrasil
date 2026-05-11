import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = REPO_ROOT / "machine" / "install-systemd-user-units.sh"


class TestSystemdUserUnits(unittest.TestCase):
    def test_dry_run_renders_units_and_enable_command(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            env = os.environ.copy()
            env["HOME"] = str(home)
            proc = subprocess.run(
                [str(INSTALLER), "--dry-run", "--enable-timers"],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )

        output = proc.stdout
        self.assertIn("== ygg-heimdall.service ==", output)
        self.assertIn("ExecStart=", output)
        self.assertIn(f"{home / '.local' / 'bin' / 'ygg'} heimdall", output)
        self.assertIn(f"WorkingDirectory={REPO_ROOT}", output)
        self.assertIn("== ygg-heimdall.timer ==", output)
        self.assertIn("OnUnitActiveSec=30m", output)
        self.assertIn("+ systemctl --user daemon-reload", output)
        self.assertIn("+ systemctl --user enable --now ygg-heimdall.timer", output)


if __name__ == "__main__":
    unittest.main()
