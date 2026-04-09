import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from ygg.semantic_registry import get_registry_item, list_registry_items

YGG_CLI = Path.home() / "ygg" / "lib" / "ygg" / "cli.py"


class TestSemanticRegistry(unittest.TestCase):
    def _write_fixture(self, root: Path) -> None:
        state_dir = root / "state" / "ygg"
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "programs.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "updatedAt": "2026-04-02T14:38:00-04:00",
                    "programs": [
                        {
                            "id": "p1",
                            "title": "Program One",
                            "status": "active",
                            "summary": "First program summary.",
                            "owner": "ian+ygg",
                        }
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (state_dir / "ideas.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "updatedAt": "2026-04-02T14:38:00-04:00",
                    "ideas": [
                        {
                            "id": "i1",
                            "title": "Idea One",
                            "status": "incubating",
                            "summary": "First idea summary.",
                            "tags": ["memory"],
                        }
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def _run_cli(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(YGG_CLI), *args, "--root", str(root)],
            capture_output=True,
            text=True,
        )

    def test_library_lists_and_finds_registry_items(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_fixture(root)

            programs = list_registry_items(root, "program")
            self.assertEqual(1, programs["version"])
            self.assertEqual("p1", programs["items"][0]["id"])

            idea = get_registry_item(root, "idea", "i1")
            self.assertEqual("Idea One", idea["title"])

    def test_program_list_and_show_support_json_and_text(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_fixture(root)

            list_json = self._run_cli(root, "program", "list", "--json")
            self.assertEqual(0, list_json.returncode)
            list_payload = json.loads(list_json.stdout)
            self.assertEqual("program", list_payload["kind"])
            self.assertEqual(1, list_payload["count"])
            self.assertEqual("p1", list_payload["items"][0]["id"])

            show_text = self._run_cli(root, "program", "show", "p1")
            self.assertEqual(0, show_text.returncode)
            self.assertIn("Ygg program", show_text.stdout)
            self.assertIn("id: p1", show_text.stdout)
            self.assertIn("owner: ian+ygg", show_text.stdout)

    def test_idea_list_and_show_support_json_and_missing_id_errors(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_fixture(root)

            list_text = self._run_cli(root, "idea", "list")
            self.assertEqual(0, list_text.returncode)
            self.assertIn("Ygg idea registry", list_text.stdout)
            self.assertIn("i1 [incubating] Idea One", list_text.stdout)

            show_json = self._run_cli(root, "idea", "show", "i1", "--json")
            self.assertEqual(0, show_json.returncode)
            show_payload = json.loads(show_json.stdout)
            self.assertEqual("idea", show_payload["kind"])
            self.assertEqual("i1", show_payload["item"]["id"])

            missing = self._run_cli(root, "idea", "show", "missing-id")
            self.assertNotEqual(0, missing.returncode)
            self.assertIn("No idea with id `missing-id`.", missing.stderr)


if __name__ == "__main__":
    unittest.main()
