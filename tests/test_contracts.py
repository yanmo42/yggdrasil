import json
import subprocess
import sys
import unittest
from pathlib import Path

YGG_CLI = Path.home() / "ygg" / "lib" / "ygg" / "cli.py"

VERBS = ["suggest", "work", "paths", "raven", "graft", "beak", "root", "branch", "resume", "forge", "promote", "status"]
REQUIRED_CONTRACT_KEYS = {
    "mutates_state",
    "requires",
    "optional",
    "writes",
    "calls",
    "guarantees",
    "fails_when",
}


class TestYggContracts(unittest.TestCase):
    def _run(self, *args: str) -> dict:
        proc = subprocess.run(
            [sys.executable, str(YGG_CLI), *args],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(proc.stdout)

    def test_help_json_lists_contract_mutability_for_every_verb(self):
        payload = self._run("help", "--json")
        verb_rows = payload["verbs"]
        self.assertEqual(sorted(v["verb"] for v in verb_rows), sorted(VERBS))
        for row in verb_rows:
            self.assertIn("mutates_state", row)

    def test_help_json_per_verb_contains_full_contract_shape(self):
        for verb in VERBS:
            with self.subTest(verb=verb):
                payload = self._run("help", verb, "--json")
                self.assertEqual(payload["verb"], verb)
                contract = payload["contract"]
                self.assertTrue(REQUIRED_CONTRACT_KEYS.issubset(contract.keys()))


if __name__ == "__main__":
    unittest.main()
