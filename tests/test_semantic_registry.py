import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from ygg.semantic_registry import (
    SemanticRegistryValidationError,
    create_registry_item,
    get_registry_item,
    list_registry_items,
    update_registry_item,
)

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
                            "relatedLanes": ["continuity"],
                            "artifacts": ["docs/program-one.md"],
                            "notes": [],
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
                            "claimTier": "plausible",
                            "origin": "ian+ygg",
                            "links": {
                                "programs": ["p1"],
                                "checkpoints": ["state/ygg/checkpoints/c1.json"],
                                "promotionTargets": ["docs/idea-one.md"],
                            },
                            "tags": ["memory"],
                            "notes": [],
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

    def test_library_create_and_update_validate_and_persist(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_fixture(root)

            created = create_registry_item(
                root,
                "program",
                {
                    "id": "p2",
                    "title": "Program Two",
                    "status": "watching",
                    "relatedLanes": ["semantic"],
                    "artifacts": ["docs/program-two.md"],
                    "notes": [],
                },
                now="2026-04-08T12:00:00-04:00",
            )
            self.assertEqual("p2", created["item"]["id"])
            self.assertEqual("2026-04-08T12:00:00-04:00", created["updatedAt"])

            updated = update_registry_item(
                root,
                "idea",
                "i1",
                {"status": "testing", "tags": ["memory", "registry"]},
                now="2026-04-08T12:05:00-04:00",
            )
            self.assertEqual("testing", updated["item"]["status"])
            self.assertEqual(["memory", "registry"], updated["item"]["tags"])

            idea = get_registry_item(root, "idea", "i1")
            self.assertEqual("testing", idea["status"])

    def test_library_rejects_duplicate_ids_and_invalid_status(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_fixture(root)

            with self.assertRaises(SemanticRegistryValidationError):
                create_registry_item(root, "program", {"id": "p1", "title": "Dup", "status": "active"})

            with self.assertRaises(SemanticRegistryValidationError):
                update_registry_item(root, "idea", "i1", {"status": "not-a-status"})

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

    def test_program_add_and_update_mutate_registry_with_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_fixture(root)

            added = self._run_cli(
                root,
                "program",
                "add",
                "--id",
                "p2",
                "--title",
                "Program Two",
                "--status",
                "watching",
                "--related-lane",
                "semantic",
                "--artifact",
                "docs/program-two.md",
                "--json",
            )
            self.assertEqual(0, added.returncode)
            added_payload = json.loads(added.stdout)
            self.assertEqual("add", added_payload["operation"])
            self.assertEqual("p2", added_payload["item"]["id"])

            updated = self._run_cli(
                root,
                "program",
                "update",
                "p2",
                "--status",
                "blocked",
                "--next-action",
                "Wait for review",
                "--json",
            )
            self.assertEqual(0, updated.returncode)
            updated_payload = json.loads(updated.stdout)
            self.assertEqual("blocked", updated_payload["item"]["status"])
            self.assertEqual("Wait for review", updated_payload["item"]["nextAction"])

            show_json = self._run_cli(root, "program", "show", "p2", "--json")
            self.assertEqual(0, show_json.returncode)
            self.assertEqual("blocked", json.loads(show_json.stdout)["item"]["status"])

    def test_program_add_rejects_duplicate_id(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_fixture(root)

            duplicate = self._run_cli(
                root,
                "program",
                "add",
                "--id",
                "p1",
                "--title",
                "Duplicate",
                "--status",
                "active",
            )
            self.assertNotEqual(0, duplicate.returncode)
            self.assertIn("program id `p1` already exists.", duplicate.stderr)

    def test_idea_add_update_and_link_mutate_registry(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_fixture(root)

            added = self._run_cli(
                root,
                "idea",
                "add",
                "--id",
                "i2",
                "--title",
                "Idea Two",
                "--status",
                "testing",
                "--claim-tier",
                "defensible",
                "--tag",
                "registry",
                "--json",
            )
            self.assertEqual(0, added.returncode)
            self.assertEqual("i2", json.loads(added.stdout)["item"]["id"])

            updated = self._run_cli(
                root,
                "idea",
                "update",
                "i2",
                "--summary",
                "Second idea summary.",
                "--origin",
                "operator",
                "--json",
            )
            self.assertEqual(0, updated.returncode)
            updated_payload = json.loads(updated.stdout)
            self.assertEqual("operator", updated_payload["item"]["origin"])

            linked = self._run_cli(
                root,
                "idea",
                "link",
                "i2",
                "--program",
                "p1",
                "--program",
                "p1",
                "--checkpoint",
                "state/ygg/checkpoints/c2.json",
                "--promotion-target",
                "docs/idea-two.md",
                "--json",
            )
            self.assertEqual(0, linked.returncode)
            linked_payload = json.loads(linked.stdout)
            self.assertEqual(["p1"], linked_payload["item"]["links"]["programs"])
            self.assertEqual(["state/ygg/checkpoints/c2.json"], linked_payload["item"]["links"]["checkpoints"])
            self.assertEqual(["docs/idea-two.md"], linked_payload["item"]["links"]["promotionTargets"])

    def test_idea_update_and_link_reject_invalid_requests(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_fixture(root)

            invalid_status = self._run_cli(root, "idea", "update", "i1", "--status", "wrong-status")
            self.assertNotEqual(0, invalid_status.returncode)
            self.assertIn("status must be one of:", invalid_status.stderr)

            missing = self._run_cli(root, "idea", "update", "missing-id", "--title", "Nope")
            self.assertNotEqual(0, missing.returncode)
            self.assertIn("No idea with id `missing-id`.", missing.stderr)

            empty_link = self._run_cli(root, "idea", "link", "i1")
            self.assertNotEqual(0, empty_link.returncode)
            self.assertIn("At least one link target is required", empty_link.stderr)


if __name__ == "__main__":
    unittest.main()
