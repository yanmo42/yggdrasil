import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from ygg.frontier import (
    build_frontier_audit,
    current_frontier_payload,
    frontier_open_payload,
    frontier_queue_path,
    frontier_registry_path,
    list_frontier_queue,
    list_frontiers,
    mark_queue_frontier_active,
    sync_frontier_queue,
)


class TestFrontierAudit(unittest.TestCase):
    def _seed_sc_repo(self, root: Path) -> None:
        files = {
            "plans/today_frontier_2026-04-06.md": "# today frontier\n",
            "plans/symbolic_maps_level4_benchmark_v0.md": "# benchmark\n",
            "docs/proof-path-ladder.md": "# ladder\n",
            "spine/concepts/SC-CONCEPT-0006.yaml": "id: SC-CONCEPT-0006\n",
            "spine/concepts/SC-CONCEPT-0008.yaml": "id: SC-CONCEPT-0008\n",
            "spine/pressure/2026-04-06/SC-PRESSURE-20260406-01.yaml": "id: SC-PRESSURE-20260406-01\n",
            "tests/test_narrative_invariants.py": "def test_placeholder():\n    pass\n",
            "nfem_suite/intelligence/narrative_invariants/symbolic_maps.py": "VALUE = 1\n",
            "plans/symbolic_maps_level4/comparison_note_v0.md": "# comparison\n",
        }
        for relative, content in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    def _seed_ygg_registry(self, root: Path) -> None:
        registry = {
            "version": 1,
            "updatedAt": "2026-04-07T09:05:00-04:00",
            "defaultTarget": "frontier:symbolic-maps-discriminating-benchmark",
            "frontiers": [
                {
                    "target": {
                        "kind": "frontier",
                        "id": "frontier:symbolic-maps-discriminating-benchmark",
                        "title": "Symbolic Maps Level-4 discriminating benchmark",
                        "status": "active",
                        "claimTier": "plausible-but-unproven",
                        "ownerSurface": "sandy-chaos",
                        "authoritativeSource": "plans/symbolic_maps_level4_benchmark_v0.md",
                    },
                    "summary": {
                        "objective": "Pressure SC-CONCEPT-0006 with a discriminating benchmark.",
                        "whyNow": "Selected by the active-frontier compression pass.",
                        "loadBearing": True,
                        "auditVerdict": "mixed",
                        "operatorReading": "Good framing; not yet benchmark-complete.",
                    },
                    "foundations": {
                        "mathematical": [],
                        "physical": [],
                        "modeling": [],
                    },
                    "gaps": {
                        "missingAssumptions": ["freeze extraction template"],
                        "missingNullModels": ["stronger baseline"],
                        "missingBenchmarks": ["not yet executed"],
                        "missingArtifacts": ["result note"],
                        "ambiguities": ["artifact 3 not fixed"],
                        "contradictionRisks": ["validated-partial wording may overstate evidence"],
                        "blockingGaps": ["no actual benchmark run yet"],
                    },
                    "dependencies": {
                        "upstream": [{"kind": "concept", "id": "SC-CONCEPT-0006", "role": "required", "status": "partial"}],
                        "downstream": [{"kind": "artifact", "id": "result note", "role": "feeds", "status": "planned"}],
                    },
                    "promotion": {
                        "readiness": "evidence-needed",
                        "dispositionHint": "TODO_PROMOTE",
                        "why": "No execution artifacts yet.",
                    },
                    "nextMove": {
                        "type": "define-foundation",
                        "action": "Freeze extraction template and run the benchmark.",
                        "why": "Turns plan into a real test.",
                        "expectedGain": "Moves toward Level 4 pressure.",
                    },
                    "handoff": {
                        "mode": "resume",
                        "domain": "ygg-dev",
                        "task": "sandy-chaos-proof-frontier-v1",
                        "why": "Existing proof-frontier baton already matches this frontier.",
                        "request": "Resume the Sandy Chaos proof-frontier lane.",
                    },
                    "evidencePlan": {
                        "docs": [
                            "plans/symbolic_maps_level4_benchmark_v0.md",
                            "plans/today_frontier_2026-04-06.md",
                            "docs/proof-path-ladder.md",
                            "spine/concepts/SC-CONCEPT-0006.yaml",
                            "spine/concepts/SC-CONCEPT-0008.yaml",
                        ],
                        "artifacts": [
                            "plans/symbolic_maps_level4_benchmark_v0.md",
                            "plans/symbolic_maps_level4/comparison_note_v0.md",
                            "tests/test_narrative_invariants.py",
                            "nfem_suite/intelligence/narrative_invariants/symbolic_maps.py",
                        ],
                        "tests": ["tests/test_narrative_invariants.py"],
                        "benchmarks": ["plans/symbolic_maps_level4_benchmark_v0.md"],
                        "spineConcepts": ["SC-CONCEPT-0006", "SC-CONCEPT-0008"],
                        "pressureEvents": ["SC-PRESSURE-20260406-01"],
                        "pressureEventPaths": ["spine/pressure/2026-04-06/SC-PRESSURE-20260406-01.yaml"],
                        "benchmarkResultCandidates": ["memory/research/symbolic_maps_level4_benchmark_v0.md"],
                    },
                }
            ],
        }
        path = frontier_registry_path(root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")

    def _seed_workspace_batons(self, workspace: Path) -> None:
        (workspace / "state" / "resume" / "tasks").mkdir(parents=True, exist_ok=True)
        index_payload = {
            "version": 1,
            "domains": {
                "ygg-dev": {
                    "activeTaskFile": "tasks/ygg-dev--sandy-chaos-proof-frontier-v1.md"
                }
            },
        }
        (workspace / "state" / "resume" / "index.json").write_text(json.dumps(index_payload, indent=2) + "\n", encoding="utf-8")

        batons = {
            "ygg-dev--sandy-chaos-proof-frontier-v1.md": """---
schemaVersion: 1
kind: task-baton
domainId: ygg-dev
taskId: sandy-chaos-proof-frontier-v1
title: Sandy Chaos Proof Frontier V1
status: active
priority: high
updatedAt: \"2026-04-07T14:44:00-04:00\"
---

## Objective

Run the active proof frontier.

## Current State

Current frontier is live.

## Next Action

Run one more bounded benchmark pass.
""",
            "ygg-dev--suggest-command.md": """---
schemaVersion: 1
kind: task-baton
domainId: ygg-dev
taskId: suggest-command
title: Suggest Command
status: active
priority: medium
updatedAt: \"2026-04-06T09:00:00-04:00\"
---

## Objective

Improve suggest routing.

## Current State

Not active right now.

## Next Action

Tighten command suggestion heuristics.
""",
            "ygg-dev--idea-capture-rhythm-v1.md": """---
schemaVersion: 1
kind: task-baton
domainId: ygg-dev
taskId: idea-capture-rhythm-v1
title: Idea Capture Rhythm V1
status: done
priority: low
updatedAt: \"2026-04-05T09:00:00-04:00\"
---

## Objective

Capture ideas.

## Current State

Done.

## Next Action

Done.
""",
        }
        for name, content in batons.items():
            (workspace / "state" / "resume" / "tasks" / name).write_text(content, encoding="utf-8")

    def test_list_frontiers_returns_registry_backed_summary(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._seed_sc_repo(root)
            self._seed_ygg_registry(root)
            payload = list_frontiers(root, ygg_root=root)
            self.assertEqual("ygg-frontier-list/v1", payload["schema"])
            self.assertEqual(1, payload["count"])
            self.assertEqual("frontier:symbolic-maps-discriminating-benchmark", payload["registry"]["defaultTarget"])
            self.assertEqual("frontier:symbolic-maps-discriminating-benchmark", payload["items"][0]["id"])
            self.assertTrue(payload["items"][0]["default"])
            self.assertEqual("mixed", payload["items"][0]["auditVerdict"])

    def test_frontier_open_payload_prefers_registered_resume_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._seed_sc_repo(root)
            self._seed_ygg_registry(root)
            payload = frontier_open_payload(root, ygg_root=root)
            self.assertEqual("ygg-frontier-open/v1", payload["schema"])
            self.assertEqual("resume", payload["openDecision"]["mode"])
            self.assertEqual(["ygg", "resume", "ygg-dev", "sandy-chaos-proof-frontier-v1"], payload["openDecision"]["command"])

    def test_current_frontier_payload_resolves_latest_frontier_note(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._seed_sc_repo(root)
            self._seed_ygg_registry(root)
            payload = current_frontier_payload(root, ygg_root=root)
            self.assertEqual("ygg-frontier-current/v1", payload["schema"])
            self.assertEqual("frontier:symbolic-maps-discriminating-benchmark", payload["target"]["id"])
            self.assertEqual("plans/today_frontier_2026-04-06.md", payload["frontierNote"])
            self.assertEqual(str(frontier_registry_path(root)), payload["registry"]["path"])

    def test_build_frontier_audit_returns_registry_backed_payload(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._seed_sc_repo(root)
            self._seed_ygg_registry(root)
            payload = build_frontier_audit(root, ygg_root=root)
            self.assertEqual(1, payload["schemaVersion"])
            self.assertEqual("ygg frontier audit", payload["generator"])
            self.assertEqual(str(frontier_registry_path(root)), payload["registry"]["path"])
            self.assertEqual("frontier:symbolic-maps-discriminating-benchmark", payload["target"]["id"])
            self.assertEqual("mixed", payload["summary"]["auditVerdict"])
            self.assertIn("SC-CONCEPT-0006", payload["evidence"]["spineConcepts"])
            self.assertIn("plans/symbolic_maps_level4_benchmark_v0.md", payload["evidence"]["benchmarks"])
            self.assertTrue(payload["gaps"]["blockingGaps"])
            self.assertEqual("evidence-needed", payload["promotion"]["readiness"])
            self.assertEqual("define-foundation", payload["nextMove"]["type"])

    def test_build_frontier_audit_upgrades_when_result_artifact_exists(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._seed_sc_repo(root)
            self._seed_ygg_registry(root)
            result_path = root / "memory/research/symbolic_maps_level4_benchmark_v0.md"
            result_path.parent.mkdir(parents=True, exist_ok=True)
            result_path.write_text("# results\n", encoding="utf-8")

            payload = build_frontier_audit(root, ygg_root=root)
            self.assertEqual("grounded", payload["summary"]["auditVerdict"])
            self.assertEqual("reviewable", payload["promotion"]["readiness"])

    def test_sync_frontier_queue_builds_queue_from_workspace_batons(self) -> None:
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as wd:
            ygg_root = Path(td)
            workspace = Path(wd)
            self._seed_workspace_batons(workspace)
            payload = sync_frontier_queue(workspace, ygg_root=ygg_root, domain="ygg-dev")
            self.assertEqual("ygg-frontier-queue-sync/v1", payload["schema"])
            self.assertEqual(3, payload["count"])
            self.assertEqual("frontier-task:ygg-dev:sandy-chaos-proof-frontier-v1", payload["activeFrontierId"])
            queue = list_frontier_queue(ygg_root)
            self.assertEqual(3, queue["count"])
            self.assertEqual(str(frontier_queue_path(ygg_root)), queue["queue"]["path"])
            self.assertEqual("active", queue["items"][0]["queueStatus"])

    def test_frontier_open_payload_prefers_queue_current_frontier(self) -> None:
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as wd:
            ygg_root = Path(td)
            workspace = Path(wd)
            self._seed_sc_repo(ygg_root)
            self._seed_ygg_registry(ygg_root)
            self._seed_workspace_batons(workspace)
            sync_frontier_queue(workspace, ygg_root=ygg_root, domain="ygg-dev")
            payload = frontier_open_payload(ygg_root, ygg_root=ygg_root)
            self.assertEqual("frontier-task:ygg-dev:sandy-chaos-proof-frontier-v1", payload["target"]["id"])
            self.assertEqual(["ygg", "resume", "ygg-dev", "sandy-chaos-proof-frontier-v1"], payload["openDecision"]["command"])

    def test_mark_queue_frontier_active_promotes_new_ready_item(self) -> None:
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as wd:
            ygg_root = Path(td)
            workspace = Path(wd)
            self._seed_workspace_batons(workspace)
            sync_frontier_queue(workspace, ygg_root=ygg_root, domain="ygg-dev")
            mark_queue_frontier_active("frontier-task:ygg-dev:suggest-command", ygg_root=ygg_root)
            queue = list_frontier_queue(ygg_root)
            active = next(row for row in queue["items"] if row["id"] == "frontier-task:ygg-dev:suggest-command")
            previous = next(row for row in queue["items"] if row["id"] == "frontier-task:ygg-dev:sandy-chaos-proof-frontier-v1")
            self.assertEqual("active", active["queueStatus"])
            self.assertEqual("ready", previous["queueStatus"])


if __name__ == "__main__":
    unittest.main()
