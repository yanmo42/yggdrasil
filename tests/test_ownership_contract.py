"""
Phase 3: ownership contract validation tests.

Goals (from plans/bridge-ownership-tightening.md):
1. Ownership categories present in inventory remain stable.
2. Command/help contracts reflect the tightened boundary.
3. No existing command falsely suggests authority it does not have.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from ygg.inventory import (
    REPO_SYSTEM_SPECS,
    build_repo_inventory,
)

YGG_CLI = Path.home() / "ygg" / "lib" / "ygg" / "cli.py"
YGG_REPO = Path.home() / "ygg"

VALID_OWNERSHIP_CLASSES = {"ygg-canonical", "ygg-derived", "assistant-local", "sc-canonical", "bridge"}

# State surfaces whose class must not drift — keyed by relative path.
EXPECTED_STATE_SURFACE_CLASSES = {
    "state/ygg/programs.json": "ygg-canonical",
    "state/ygg/ideas.json": "ygg-canonical",
    "state/ygg/checkpoints": "ygg-canonical",
    "state/runtime/persona-mode.json": "assistant-local",
    "state/runtime/promotions.jsonl": "ygg-derived",
    "state/runtime/ygg-self.json": "assistant-local",
    "state/runtime/ygg-kernel.json": "assistant-local",
    "state/runtime/event-queue.jsonl": "ygg-derived",
    "state/runtime/promotion-candidates.jsonl": "ygg-derived",
}

# Commands that mutate ygg-canonical state. Their contracts must declare `writes`.
CANONICAL_MUTATING_VERBS = {"checkpoint", "promote"}

# Commands that are bridges. Their writes should not include state/ygg/ paths.
BRIDGE_VERBS = {"ratatoskr"}

# Paths that only ygg-canonical commands may write. Bridge/runtime-only commands must not
# declare writes into these paths without a defensible contract reason.
YGG_CANONICAL_PATH_PREFIXES = (
    "state/ygg/",
    "~/ygg/state/ygg/",
)


def _run_cli(*args: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(YGG_CLI), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(proc.stdout)


def _build_full_temp_repo() -> tuple[Path, "tempfile.TemporaryDirectory"]:
    """Create a minimal temp repo with the files needed for full inventory."""
    td = tempfile.TemporaryDirectory()
    root = Path(td.name)

    dirs = ["state/ygg/checkpoints", "links"]
    for d in dirs:
        (root / d).mkdir(parents=True, exist_ok=True)

    files = [
        "lib/ygg/cli.py",
        "bin/ygg",
        "commands/README.md",
        "README.md",
        "lib/ygg/continuity.py",
        "state/ygg/programs.json",
        "state/ygg/ideas.json",
        "lib/ygg/heimdall.py",
        "lib/ygg/ratatoskr.py",
        "state/runtime/promotions.jsonl",
        "state/notes/promotions.md",
        "lib/ygg/path_contract.py",
        "lib/ygg/bootstrap_registry.py",
        "state/templates/ygg-paths.yaml.template",
        "state/profiles/components.yaml",
        "lib/ygg/ravens_v1.py",
        "docs/RAVENS.md",
        "docs/RAVENS-V1.md",
        "docs/BRIDGE-OWNERSHIP-CONTRACT.md",
        "state/README.md",
        "state/policy/STATE-BOUNDARY.md",
        "state/scripts/spine-backup.sh",
        "state/scripts/spine-restore.sh",
        "tests/test_contracts.py",
        "tests/test_continuity.py",
        "tests/test_heimdall.py",
        "tests/test_ratatoskr.py",
        "tests/test_bootstrap_inspect.py",
        "tests/test_bootstrap_profiles.py",
        "tests/test_bootstrap_registry.py",
        "tests/test_ravens.py",
        "docs/ROADMAP.md",
        "docs/NORTH-STAR.md",
    ]
    for rel in files:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x\n", encoding="utf-8")

    (root / "state/ygg/programs.json").write_text('{"programs":[{"id":"p1"}]}\n', encoding="utf-8")
    (root / "state/ygg/ideas.json").write_text('{"ideas":[{"id":"i1"}]}\n', encoding="utf-8")
    (root / "links/planner.py").write_text("bridge\n", encoding="utf-8")

    # State surfaces that carry ownership labels
    state_runtime_files = [
        "state/runtime/persona-mode.json",
        "state/runtime/ygg-self.json",
        "state/runtime/ygg-kernel.json",
        "state/runtime/event-queue.jsonl",
        "state/runtime/promotion-candidates.jsonl",
    ]
    for rel in state_runtime_files:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")

    return root, td


# ---------------------------------------------------------------------------
# 1. REPO_SYSTEM_SPECS stability
# ---------------------------------------------------------------------------

class TestSystemSpecOwnershipStability(unittest.TestCase):
    """Every system spec must declare a valid, stable ownershipClass."""

    def test_every_system_spec_has_ownership_class(self):
        for spec in REPO_SYSTEM_SPECS:
            with self.subTest(spec_id=spec["id"]):
                self.assertIn(
                    "ownershipClass",
                    spec,
                    f"System spec '{spec['id']}' is missing ownershipClass.",
                )

    def test_every_system_spec_ownership_class_is_valid(self):
        for spec in REPO_SYSTEM_SPECS:
            with self.subTest(spec_id=spec["id"]):
                cls = spec.get("ownershipClass", "")
                self.assertIn(
                    cls,
                    VALID_OWNERSHIP_CLASSES,
                    f"System spec '{spec['id']}' has unknown ownershipClass '{cls}'.",
                )

    def test_event_routing_courier_is_bridge(self):
        spec = next(s for s in REPO_SYSTEM_SPECS if s["id"] == "event-routing-courier")
        self.assertEqual(
            spec["ownershipClass"],
            "bridge",
            "event-routing-courier must be classified as 'bridge' — it routes across the ownership boundary.",
        )

    def test_semantic_continuity_kernel_is_ygg_canonical(self):
        spec = next(s for s in REPO_SYSTEM_SPECS if s["id"] == "semantic-continuity-kernel")
        self.assertEqual(spec["ownershipClass"], "ygg-canonical")

    def test_cli_control_plane_is_ygg_canonical(self):
        spec = next(s for s in REPO_SYSTEM_SPECS if s["id"] == "cli-control-plane")
        self.assertEqual(spec["ownershipClass"], "ygg-canonical")


# ---------------------------------------------------------------------------
# 2. Inventory output — ownership fields surface correctly
# ---------------------------------------------------------------------------

class TestInventoryOwnershipOutput(unittest.TestCase):
    """Inventory JSON must carry ownershipClass on systems, state surfaces, and bridges."""

    def setUp(self):
        self._root, self._td = _build_full_temp_repo()

    def tearDown(self):
        self._td.cleanup()

    def test_systems_carry_ownership_class(self):
        payload = build_repo_inventory(self._root)
        for row in payload["systems"]:
            with self.subTest(system_id=row["id"]):
                self.assertIn(
                    "ownershipClass",
                    row,
                    f"System '{row['id']}' missing ownershipClass in inventory output.",
                )
                self.assertIn(row["ownershipClass"], VALID_OWNERSHIP_CLASSES)

    def test_state_surfaces_carry_ownership_class(self):
        payload = build_repo_inventory(self._root)
        for row in payload["stateSurfaces"]:
            with self.subTest(path=row["relativePath"]):
                self.assertIn(
                    "ownershipClass",
                    row,
                    f"State surface '{row['relativePath']}' missing ownershipClass.",
                )
                self.assertIn(row["ownershipClass"], VALID_OWNERSHIP_CLASSES)

    def test_state_surface_classes_match_contract(self):
        payload = build_repo_inventory(self._root)
        surface_by_path = {row["relativePath"]: row for row in payload["stateSurfaces"]}
        for rel_path, expected_class in EXPECTED_STATE_SURFACE_CLASSES.items():
            if rel_path not in surface_by_path:
                continue  # surface not present in this temp repo — skip
            actual = surface_by_path[rel_path].get("ownershipClass")
            self.assertEqual(
                actual,
                expected_class,
                f"State surface '{rel_path}' should be '{expected_class}', got '{actual}'.",
            )

    def test_ygg_state_surfaces_are_canonical(self):
        payload = build_repo_inventory(self._root)
        for row in payload["stateSurfaces"]:
            rel = row["relativePath"]
            if rel.startswith("state/ygg/"):
                self.assertEqual(
                    row.get("ownershipClass"),
                    "ygg-canonical",
                    f"'{rel}' is under state/ygg/ and must be ygg-canonical.",
                )

    def test_runtime_state_surfaces_are_not_canonical(self):
        payload = build_repo_inventory(self._root)
        for row in payload["stateSurfaces"]:
            rel = row["relativePath"]
            if rel.startswith("state/runtime/"):
                cls = row.get("ownershipClass")
                self.assertNotEqual(
                    cls,
                    "ygg-canonical",
                    f"'{rel}' is runtime state and must not be labeled ygg-canonical.",
                )

    def test_bridge_rows_carry_bridge_class(self):
        payload = build_repo_inventory(self._root)
        for row in payload["bridges"]:
            with self.subTest(path=row["relativePath"]):
                self.assertEqual(
                    row.get("ownershipClass"),
                    "bridge",
                    f"Bridge entry '{row['relativePath']}' must have ownershipClass='bridge'.",
                )

    def test_ownership_contract_path_present_when_doc_exists(self):
        payload = build_repo_inventory(self._root)
        self.assertIsNotNone(
            payload.get("ownershipContract"),
            "Inventory must include 'ownershipContract' when docs/BRIDGE-OWNERSHIP-CONTRACT.md exists.",
        )

    def test_ownership_contract_path_none_when_doc_missing(self):
        root2, td2 = _build_full_temp_repo()
        try:
            (root2 / "docs" / "BRIDGE-OWNERSHIP-CONTRACT.md").unlink(missing_ok=True)
            payload = build_repo_inventory(root2)
            self.assertIsNone(
                payload.get("ownershipContract"),
                "ownershipContract must be None when the contract doc is absent.",
            )
        finally:
            td2.cleanup()


# ---------------------------------------------------------------------------
# 3. Command contracts — mutation authority checks
# ---------------------------------------------------------------------------

class TestCommandContractMutationAuthority(unittest.TestCase):
    """Commands must not imply cross-domain mutation authority they do not have."""

    def _contract(self, verb: str) -> dict:
        payload = _run_cli("help", verb, "--json")
        return payload["contract"]

    def test_canonical_mutating_verbs_declare_writes(self):
        """Commands that mutate ygg-canonical state must declare their writes."""
        for verb in CANONICAL_MUTATING_VERBS:
            with self.subTest(verb=verb):
                contract = self._contract(verb)
                writes = contract.get("writes") or []
                self.assertTrue(
                    len(writes) > 0,
                    f"'{verb}' mutates ygg-canonical state but declares no writes in its contract.",
                )

    def test_bridge_verbs_do_not_claim_canonical_writes(self):
        """Bridge commands must not list ygg-canonical paths (state/ygg/) as writes."""
        for verb in BRIDGE_VERBS:
            with self.subTest(verb=verb):
                contract = self._contract(verb)
                writes = contract.get("writes") or []
                for write_path in writes:
                    for prefix in YGG_CANONICAL_PATH_PREFIXES:
                        self.assertFalse(
                            write_path.startswith(prefix),
                            f"Bridge verb '{verb}' falsely claims write authority over "
                            f"ygg-canonical path '{write_path}'.",
                        )

    def test_inventory_does_not_mutate_state(self):
        """inventory is read-only and must not claim mutates_state=True."""
        contract = self._contract("inventory")
        self.assertFalse(
            contract.get("mutates_state"),
            "'inventory' must not claim mutates_state — it is a read-only surface.",
        )

    def test_retrieve_does_not_mutate_state(self):
        """retrieve is read-only."""
        contract = self._contract("retrieve")
        self.assertFalse(
            contract.get("mutates_state"),
            "'retrieve' must not claim mutates_state.",
        )

    def test_suggest_does_not_mutate_state(self):
        """suggest is advisory only."""
        contract = self._contract("suggest")
        self.assertFalse(
            contract.get("mutates_state"),
            "'suggest' must not claim mutates_state — it is advisory only.",
        )

    def test_read_only_verbs_do_not_claim_mutation(self):
        """Verbs that are purely read-only must have mutates_state=False (not indirect/sometimes)."""
        # frontier/resume/root are "indirect" — excluded here by design.
        # nyx is "sometimes" — excluded here by design.
        strictly_read_only = {"inventory", "retrieve", "retrieve-benchmark", "suggest", "status", "paths", "bootstrap"}
        payload = _run_cli("help", "--json")
        for row in payload["verbs"]:
            if row["verb"] in strictly_read_only:
                self.assertIs(
                    row.get("mutates_state"),
                    False,
                    f"Read-only verb '{row['verb']}' must have mutates_state=False, "
                    f"got {row.get('mutates_state')!r}.",
                )


if __name__ == "__main__":
    unittest.main()
