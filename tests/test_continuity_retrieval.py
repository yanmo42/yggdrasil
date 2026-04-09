import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from ygg.continuity_corpus import load_continuity_corpus
from ygg.continuity_retrieval import rank_records, run_benchmark
from ygg.continuity_topology import build_continuity_topology

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "continuity_state"
BENCHMARK_FILE = REPO_ROOT / "tests" / "fixtures" / "continuity_benchmark.json"
YGG_CLI = REPO_ROOT / "lib" / "ygg" / "cli.py"


class TestContinuityRetrieval(unittest.TestCase):
    def test_normalizes_all_target_surfaces(self) -> None:
        records = load_continuity_corpus(FIXTURE_ROOT)
        self.assertEqual(10, len(records))
        kinds = {record.kind for record in records}
        self.assertEqual({"checkpoint", "idea", "program", "event", "promotion"}, kinds)

        idea = next(record for record in records if record.id == "idea:topology-aware-continuity-retrieval")
        self.assertIn("program:ygg-continuity-integration", idea.links)
        self.assertIn("checkpoint:2026-04-02T09-30-00+00-00_topological-memory", idea.links)

    def test_builds_explicit_and_inferred_topology(self) -> None:
        records = load_continuity_corpus(FIXTURE_ROOT)
        topology = build_continuity_topology(records)
        edges = topology["edges"]
        edge_types = {edge["type"] for edge in edges}
        self.assertIn("idea-program", edge_types)
        self.assertIn("idea-checkpoint", edge_types)
        self.assertIn("program-lane", edge_types)
        self.assertIn("shared-tag", edge_types)

    def test_topology_strategy_surfaces_linked_program_for_idea_query(self) -> None:
        records = load_continuity_corpus(FIXTURE_ROOT)
        topology = build_continuity_topology(records)
        recency = rank_records("topology-aware continuity retrieval", records, topology, strategy="recency", limit=3)
        hybrid = rank_records("topology-aware continuity retrieval", records, topology, strategy="topology", limit=3)
        recency_ids = [row.record.id for row in recency]
        hybrid_ids = [row.record.id for row in hybrid]
        self.assertIn("idea:topology-aware-continuity-retrieval", hybrid_ids[:1])
        self.assertIn("program:ygg-continuity-integration", hybrid_ids)
        self.assertNotIn("program:ygg-continuity-integration", recency_ids[:1])

    def test_benchmark_runner_reports_strategy_scores(self) -> None:
        payload = run_benchmark(FIXTURE_ROOT, BENCHMARK_FILE, limit=3)
        self.assertEqual(5, payload["caseCount"])
        self.assertIn("topology", payload["strategies"])
        self.assertGreaterEqual(
            payload["strategies"]["topology"]["averageScore"],
            payload["strategies"]["recency"]["averageScore"],
        )

    def test_cli_retrieve_and_benchmark_json_modes(self) -> None:
        retrieve = subprocess.run(
            [
                sys.executable,
                str(YGG_CLI),
                "retrieve",
                "runtime embodiment changed",
                "--root",
                str(FIXTURE_ROOT),
                "--json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        retrieve_payload = json.loads(retrieve.stdout)
        self.assertEqual("topology", retrieve_payload["strategy"])
        self.assertEqual("event:evt_runtime_changed", retrieve_payload["results"][0]["record"]["id"])

        benchmark = subprocess.run(
            [
                sys.executable,
                str(YGG_CLI),
                "retrieve-benchmark",
                "--root",
                str(FIXTURE_ROOT),
                "--benchmark",
                str(BENCHMARK_FILE),
                "--json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        benchmark_payload = json.loads(benchmark.stdout)
        self.assertEqual(5, benchmark_payload["caseCount"])
        self.assertIn("keyword", benchmark_payload["strategies"])


if __name__ == "__main__":
    unittest.main()
