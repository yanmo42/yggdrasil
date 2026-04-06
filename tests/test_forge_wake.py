import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from ygg import cli


class TestForgeWorkerCommand(unittest.TestCase):
    def test_build_forge_worker_command_includes_wake_hook(self) -> None:
        cmd = cli._build_forge_worker_command(
            domain="ygg-dev",
            task="wake-flow",
            request="Implement the next Ygg wake-path step.",
            cwd="/tmp/ygg-test",
            openclaw_bin="openclaw",
            wake_now=True,
        )

        self.assertIn("codex -C /tmp/ygg-test exec --full-auto", cmd)
        self.assertIn("Continue the ygg-dev/wake-flow lane.", cmd)
        self.assertIn("openclaw system event --text", cmd)
        self.assertIn("--mode now", cmd)
        self.assertIn("summarize changes, validation status, and next step", cmd)

    def test_build_forge_worker_command_can_skip_wake_hook(self) -> None:
        cmd = cli._build_forge_worker_command(
            domain="ygg-dev",
            task="wake-flow",
            request="Implement the next Ygg wake-path step.",
            cwd="/tmp/ygg-test",
            openclaw_bin="openclaw",
            wake_now=False,
        )

        self.assertIn("codex -C /tmp/ygg-test exec --full-auto", cmd)
        self.assertNotIn("openclaw system event", cmd)

    def test_cmd_forge_print_worker_command_emits_shell_ready_command(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(
            [
                "forge",
                "--domain",
                "ygg-dev",
                "--task",
                "wake-flow",
                "--print-worker-command",
                "--wake-now",
                "--cwd",
                "/tmp/ygg-test",
                "implement",
                "the",
                "next",
                "step",
            ]
        )

        with mock.patch.object(cli, "_resolve_target", return_value=("ygg-dev", "wake-flow")):
            out = io.StringIO()
            with redirect_stdout(out):
                rc = cli.cmd_forge(args)

        self.assertEqual(rc, 0)
        text = out.getvalue()
        self.assertIn("codex -C /tmp/ygg-test exec --full-auto", text)
        self.assertIn("openclaw system event --text", text)
        self.assertIn("Done: ygg-dev/wake-flow;", text)


if __name__ == "__main__":
    unittest.main()
