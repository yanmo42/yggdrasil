import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from ygg.inventory import build_inventory, build_repo_inventory


class TestHostInventory(unittest.TestCase):
    def _write_contract(self, home: Path) -> Path:
        contract = home / "ygg-paths.yaml"
        workspace = home / ".openclaw" / "workspace-claw-main"
        ygg_root = home / "ygg"
        projects = home / "projects"
        sandy = projects / "sandy-chaos"
        site = projects / "ianmoog-site"
        workspace.mkdir(parents=True, exist_ok=True)
        ygg_root.mkdir(parents=True, exist_ok=True)
        sandy.mkdir(parents=True, exist_ok=True)
        site.mkdir(parents=True, exist_ok=True)

        contract.write_text(
            "\n".join(
                [
                    "schema: ygg-paths/v1",
                    "profile: test",
                    "paths:",
                    "  spine:",
                    f"    root: {workspace}",
                    "  control_plane:",
                    "    name: ygg",
                    f"    root: {ygg_root}",
                    f"    bin: {ygg_root / 'bin' / 'ygg'}",
                    "  work_repos:",
                    f"    root: {projects}",
                    f"    sandy-chaos: {sandy}",
                    f"    ianmoog-site: {site}",
                    "contracts:",
                    "  canonical_state_owner: spine",
                    f"  canonical_path_registry: {contract}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        return contract

    def test_inventory_classifies_core_optional_runtime_and_secret_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            contract = self._write_contract(home)

            (home / "tara" / ".git").mkdir(parents=True)
            (home / "ygg" / ".git").mkdir(parents=True)
            (home / ".openclaw" / "workspace-claw-main" / ".git").mkdir(parents=True)
            (home / "projects" / "sandy-chaos" / ".git").mkdir(parents=True)
            (home / "projects" / "ianmoog-site" / ".git").mkdir(parents=True)
            (home / "projects" / "nyx-nlp" / ".git").mkdir(parents=True)
            (home / ".claude").mkdir(parents=True)
            (home / ".codex").mkdir(parents=True)
            (home / ".ollama").mkdir(parents=True)
            (home / ".openclaw" / "agents").mkdir(parents=True)
            (home / ".openclaw" / "browser").mkdir(parents=True)
            (home / ".openclaw" / "memory").mkdir(parents=True)
            (home / ".openclaw" / "tasks").mkdir(parents=True)
            (home / ".cache").mkdir(parents=True)
            (home / ".npm").mkdir(parents=True)
            (home / ".npm-global").mkdir(parents=True)
            (home / ".vscode-server").mkdir(parents=True)
            (home / ".config" / "systemd" / "user").mkdir(parents=True)
            (home / ".config" / "gh").mkdir(parents=True)
            (home / ".config" / "ygg").mkdir(parents=True)
            (home / "projects" / "_assistant_home_legacy_20260307-203553").mkdir(parents=True)
            (home / ".zshrc").write_text("export OPENROUTER_API_KEY=test\n", encoding="utf-8")
            (home / ".gitconfig").write_text("[user]\n\tname = test\n", encoding="utf-8")
            (home / ".config" / "starship.toml").write_text("format = '$directory'\n", encoding="utf-8")
            (home / ".openclaw" / "openclaw.json").write_text("{}", encoding="utf-8")
            (home / ".codex" / "auth.json").write_text("{}", encoding="utf-8")
            (home / ".claude" / ".credentials.json").write_text("{}", encoding="utf-8")
            (home / ".config" / "gh" / "hosts.yml").write_text("{}", encoding="utf-8")
            (home / ".config" / "ygg" / "backup.key").write_text("secret", encoding="utf-8")

            payload = build_inventory(home, path_override=contract)
            classification = payload["classification"]

            core_paths = {row["relativePath"] for row in classification["coreCandidates"]}
            self.assertIn("ygg", core_paths)
            self.assertIn(".openclaw/workspace-claw-main", core_paths)

            protocol_paths = {row["relativePath"] for row in classification["protocolContracts"]}
            self.assertIn("tara", protocol_paths)

            template_paths = {row["relativePath"] for row in classification["templateCandidates"]}
            self.assertIn(".zshrc", template_paths)
            self.assertIn(".config/systemd/user", template_paths)

            docs_paths = {row["relativePath"] for row in classification["documentationSurfaces"]}
            self.assertIn("projects/ianmoog-site", docs_paths)

            optional_paths = {row["relativePath"] for row in classification["optionalProjects"]}
            self.assertIn("projects/sandy-chaos", optional_paths)
            self.assertIn("projects/nyx-nlp", optional_paths)

            legacy_paths = {row["relativePath"] for row in classification["legacySurfaces"]}
            self.assertIn("projects/_assistant_home_legacy_20260307-203553", legacy_paths)

            runtime_paths = {row["relativePath"] for row in classification["runtimeState"]}
            self.assertIn(".claude", runtime_paths)
            self.assertIn(".codex", runtime_paths)
            self.assertIn(".openclaw/memory", runtime_paths)

            disposable_paths = {row["relativePath"] for row in classification["disposableCaches"]}
            self.assertIn(".cache", disposable_paths)
            self.assertIn(".npm", disposable_paths)

            secret_paths = {row["relativePath"] for row in classification["secretSurfaces"]}
            self.assertIn(".zshrc", secret_paths)
            self.assertIn(".openclaw/openclaw.json", secret_paths)
            self.assertIn(".codex/auth.json", secret_paths)

            repo_paths = {row["relativePath"] for row in payload["gitRepos"]}
            self.assertIn("ygg", repo_paths)
            self.assertIn("projects/nyx-nlp", repo_paths)


    def test_repo_inventory_reports_systems_bridges_and_next_targets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for relative in [
                "state/ygg/checkpoints",
            ]:
                (root / relative).mkdir(parents=True, exist_ok=True)

            for relative in [
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
            ]:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("x\n", encoding="utf-8")

            links_dir = root / "links"
            links_dir.mkdir(parents=True, exist_ok=True)
            (links_dir / "README.md").write_text("links\n", encoding="utf-8")
            (links_dir / "planner.py").write_text("bridge\n", encoding="utf-8")
            (root / "state/ygg/programs.json").write_text('{"programs":[{"id":"p1"}]}\n', encoding="utf-8")
            (root / "state/ygg/ideas.json").write_text('{"ideas":[{"id":"i1"}]}\n', encoding="utf-8")

            payload = build_repo_inventory(root)
            self.assertEqual("ygg-repo-inventory/v1", payload["schema"])
            self.assertIn("inventory", payload["commandSurface"])
            system_ids = {row["id"] for row in payload["systems"]}
            self.assertIn("cli-control-plane", system_ids)
            self.assertIn("semantic-continuity-kernel", system_ids)
            self.assertIn("runtime-embodiment-refresh", system_ids)
            self.assertIn("event-routing-courier", system_ids)
            bridge_paths = {row["relativePath"] for row in payload["bridges"]}
            self.assertIn("links/planner.py", bridge_paths)
            state_paths = {row["relativePath"] for row in payload["stateSurfaces"]}
            self.assertIn("state/ygg/programs.json", state_paths)
            self.assertIn("state/ygg/ideas.json", state_paths)
            speculative_ids = {row["id"] for row in payload["speculativeTracks"]}
            self.assertIn("response-cards-and-qa-layer", speculative_ids)
            next_target_ids = {row["id"] for row in payload["nextTargets"]}
            self.assertIn("semantic-registry-ops", next_target_ids)
            self.assertIn("bridge-ownership-tightening", next_target_ids)


if __name__ == "__main__":
    unittest.main()
