#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path

_SELF = Path(__file__).resolve()
_LIB_ROOT = _SELF.parents[1]
if str(_LIB_ROOT) not in sys.path:
    sys.path.insert(0, str(_LIB_ROOT))

from ygg.continuity import (
    ALLOWED_DISPOSITIONS as CONTINUITY_DISPOSITIONS,
    PROMOTION_DISPOSITIONS,
    load_latest_checkpoint,
    write_checkpoint as write_continuity_checkpoint,
)
from ygg.bootstrap_registry import (
    load_registry,
    parse_profile_env,
    read_package_manifest,
    render_path_contract,
    resolve_registry_assignments,
)
from ygg.heimdall import main as heimdall_main
from ygg.inventory import build_repo_inventory
from ygg.path_contract import RuntimePaths, resolve_runtime_paths, runtime_payload, validate_runtime_paths
from ygg.ravens_v1 import (
    adjudicate_flight,
    create_return_packet,
    ensure_raven_dirs,
    launch_flight,
    list_flights,
    load_flight,
    load_flight_log,
    parse_actors,
    propose_beak,
    propose_graft,
    record_aviary_exchange,
    record_probe,
)
from ygg.ratatoskr import main as ratatoskr_main

HOME = Path.home()
RUNTIME_PATHS: RuntimePaths = resolve_runtime_paths()
PATH_CONTRACT_FILE = RUNTIME_PATHS.contract_path
YGG_HOME = RUNTIME_PATHS.control_plane_root
WORKSPACE = RUNTIME_PATHS.spine_root
WORK_SCRIPT = WORKSPACE / "scripts" / "work.py"
RESUME_SCRIPT = WORKSPACE / "scripts" / "resume.py"
STATE_DIR = YGG_HOME / "state" / "runtime"
NOTES_DIR = YGG_HOME / "state" / "notes"
PROMOTION_LOG_JSONL = STATE_DIR / "promotions.jsonl"
PROMOTION_LOG_MD = NOTES_DIR / "promotions.md"
PERSONA_MODE_FILE = STATE_DIR / "persona-mode.json"
WORKSPACE_PERSONA_MODE_FILE = WORKSPACE / "state" / "persona-mode.json"
RAVEN_STATE_DIR = STATE_DIR
DEFAULT_SESSION = "planner--main"
DEFAULT_OPENCLAW_BIN = "openclaw"
PROFILE_DIR = YGG_HOME / "state" / "profiles"
DEFAULT_BOOTSTRAP_PROFILE = os.environ.get("BOOTSTRAP_PROFILE", "stable")
DEFAULT_COMPONENT_REGISTRY = PROFILE_DIR / "components.yaml"

if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

try:
    from tools.work_v1.planner import build_planner_boot_packet, load_active_tasks
    from tools.work_v1.router import RouteSuggestion, classify_request
except Exception as exc:  # pragma: no cover - friendly runtime guard
    build_planner_boot_packet = None
    load_active_tasks = None
    RouteSuggestion = None
    classify_request = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


SUGGESTION_BLURBS = {
    "work": "Let the planner interpret the request and keep spine oversight.",
    "root": "Stay in the planner explicitly before committing to a route.",
    "branch": "Create a new explicit lane when the work is separate.",
    "resume": "Reopen the lane with baton-aware continuity context.",
    "forge": "Bias the planner toward implementation/delegation for a specific lane.",
    "status": "Inspect the currently active lanes before choosing.",
}

EXPLAIN_CARDS = {
    "suggest": {
        "purpose": "Translate natural-language intent into explicit candidate Ygg commands.",
        "when_to_use": [
            "When you know what you want but not which Ygg verb to run.",
            "When you want explainable options before execution.",
        ],
        "examples": [
            'ygg suggest "implement the improved theme selector UX"',
            'ygg suggest --domain website-dev --task theme-selector-enhancements "implement the improved theme selector UX"',
            'ygg suggest --json "continue website work"',
        ],
        "next": ["work", "resume", "forge", "branch"],
    },
    "work": {
        "purpose": "Open the default Ygg front door for continuity-aware planning, with optional soft natural-language resolution.",
        "when_to_use": [
            "When route/target is still unclear.",
            "When you want planner oversight by default.",
            "When you want Ygg to assemble continuity before execution choices.",
            "When you want the main human entrypoint rather than a lower-level control verb.",
        ],
        "examples": [
            'ygg work',
            'ygg work "add more functionality to theme selector in personal website"',
            'ygg work "continue the Sandy Chaos constraints lane"',
        ],
        "next": ["suggest", "root", "status"],
    },
    "paths": {
        "purpose": "Inspect or validate path-contract resolution for Ygg/OpenClaw roots.",
        "when_to_use": [
            "When verifying host portability and path wiring.",
            "When debugging workspace/control-plane path drift.",
        ],
        "examples": ["ygg paths", "ygg paths check", "ygg paths check --json"],
        "next": ["status", "work"],
    },
    "bootstrap": {
        "purpose": "Inspect the resolved bootstrap profile, component registry, package manifests, and rendered path-contract preview.",
        "when_to_use": [
            "When you want to see what a stable/dev bootstrap would actually do before running it.",
            "When reviewing component roots, refs, enablement, or package manifests from inside Ygg.",
        ],
        "examples": [
            "ygg bootstrap inspect",
            "ygg bootstrap inspect --profile dev --json",
        ],
        "next": ["paths", "status", "work"],
    },
    "inventory": {
        "purpose": "Produce a structured inventory of the Ygg repo itself: implemented systems, bridges, state surfaces, speculative tracks, and next build targets.",
        "when_to_use": [
            "When the repo feels overgrown and you need an executable map instead of more theory.",
            "When deciding what is implemented, partial, bridge-owned, or still speculative.",
        ],
        "examples": [
            "ygg inventory",
            "ygg inventory --json",
            "ygg inventory --root ~/ygg",
        ],
        "next": ["status", "bootstrap", "paths"],
    },
    "root": {
        "purpose": "Force direct planner-spine entry with no aggressive route guess.",
        "when_to_use": [
            "When ambiguity is high and you want explicit planning first.",
            "When you want spine control without implicit routing pressure.",
        ],
        "examples": ['ygg root "help me decide the next move"', 'ygg root --print-packet "help me plan"'],
        "next": ["work", "branch", "forge"],
    },
    "branch": {
        "purpose": "Create or refresh an explicit lane in baton state.",
        "when_to_use": [
            "When work is separate from current active lanes.",
            "When you want inspectable continuity for a new effort.",
        ],
        "examples": [
            'ygg branch website-dev theme-selector-enhancements --objective "Add more functionality to the theme selector"',
            'ygg branch demo-domain demo-task --dry-run',
        ],
        "next": ["resume", "forge", "promote"],
    },
    "resume": {
        "purpose": "Reopen a lane with baton-aware continuity context.",
        "when_to_use": [
            "When continuity is the main concern.",
            "When you want the latest objective/next-action state before acting.",
        ],
        "examples": [
            "ygg resume website-dev theme-selector-enhancements",
            "ygg resume website-dev theme-selector-enhancements --print-only",
        ],
        "next": ["forge", "promote", "status"],
    },
    "forge": {
        "purpose": "Bias planner routing toward implementation/delegation for a specific lane, or print a ready worker command.",
        "when_to_use": [
            "When the next move is coding/build/fix execution.",
            "When you want implementation posture while preserving planner oversight.",
            "When you want Ygg to emit a ready-to-run Codex command with wake behavior baked in.",
            "When you need an explicit lower-level execution control instead of the general front door.",
        ],
        "examples": [
            'ygg forge --domain website-dev --task theme-selector-enhancements "implement the improved theme selector UX"',
            "ygg forge --domain website-dev --task theme-selector-enhancements --print-packet",
            "ygg forge --domain ygg-dev --task sandy-chaos-alignment-constraints-v1 --print-worker-command --wake-now",
        ],
        "next": ["promote", "status", "resume"],
    },
    "checkpoint": {
        "purpose": "Write a Sandy Chaos continuity checkpoint into canonical Ygg control-plane state.",
        "when_to_use": [
            "When you want a minimal lane summary with explicit disposition.",
            "When bridging SC continuity artifacts into Ygg without baton edits.",
        ],
        "examples": [
            'ygg checkpoint --lane bridge --summary "Kernel ported" --disposition LOG_ONLY',
            'ygg checkpoint --lane bridge --summary "Needs docs" --disposition DOC_PROMOTE --promotion-target docs/CONTINUITY-OPS-V1.md',
        ],
        "next": ["status", "promote"],
    },
    "promote": {
        "purpose": "Record either a baton promotion event or an SC continuity promotion checkpoint.",
        "when_to_use": [
            "When a branch produced a meaningful result.",
            "When you want a durable log of what happened next.",
        ],
        "examples": [
            'ygg promote website-dev theme-selector-enhancements --disposition log-daily --note "Scope clarified"',
            'ygg promote --lane bridge --summary "Promote to docs" --disposition DOC_PROMOTE --promotion-target docs/CONTINUITY-OPS-V1.md',
            "ygg promote website-dev theme-selector-enhancements --disposition log-daily --dry-run",
        ],
        "next": ["status", "resume"],
    },
    "status": {
        "purpose": "Inspect tracked baton state or the latest SC continuity checkpoint.",
        "when_to_use": [
            "When choosing which lane to target.",
            "When checking current baton state quickly.",
        ],
        "examples": ["ygg status", "ygg status website-dev", "ygg status --continuity"],
        "next": ["suggest", "resume", "branch"],
    },
    "raven": {
        "purpose": "Run RAVENS v1 flight operations (launch/status/inspect/return).",
        "when_to_use": [
            "When you want inspectable roaming-cognition flights.",
            "When you need a governed return packet tied to evidence.",
        ],
        "examples": [
            'ygg raven launch --trigger human-request "Inspect env for package drift"',
            "ygg raven status",
            "ygg raven inspect <flight-id>",
            "ygg raven return <flight-id>",
            "ygg raven adjudicate <flight-id> ADOPT",
        ],
        "next": ["graft", "beak", "status"],
    },
    "graft": {
        "purpose": "Propose additive structural growth artifacts (proposal only).",
        "when_to_use": [
            "When adding new branches/protocols/adapters to Ygg.",
            "When recording a lawful-growth proposal from raven findings.",
        ],
        "examples": ['ygg graft propose "Add proposal gate protocol" --target-attachment state/policy/'],
        "next": ["raven", "status"],
    },
    "beak": {
        "purpose": "Propose subtractive/reshaping actions (proposal only; no execution).",
        "when_to_use": [
            "When identifying deadwood/duplication/drift for potential pruning.",
            "When you need a structured soft/hard beak proposal for governance.",
        ],
        "examples": ['ygg beak propose "Deprecate duplicate lane docs" --target docs/ --problem-type duplication'],
        "next": ["raven", "status"],
    },
    "mode": {
        "purpose": "Persist or inspect persona-mode override state for Solace/Nyx, with optional live session notification.",
        "when_to_use": [
            "When you want Nyx or Solace to stay foregrounded beyond a single prompt.",
            "When you want a small command-surface switch instead of typing mode directives manually.",
        ],
        "examples": [
            "ygg mode nyx",
            "ygg mode solace",
            "ygg mode get",
            "ygg mode clear",
        ],
        "next": ["run", "status", "work", "root"],
    },
    "run": {
        "purpose": "Friendly alias for fast mode control, especially `ygg run nyx`.",
        "when_to_use": [
            "When you want the shortest command for switching foreground persona.",
            "When you want `run` to act like an imperative front door instead of remembering `mode` syntax.",
        ],
        "examples": [
            "ygg run nyx",
            "ygg run solace",
            "ygg run auto",
            "ygg run get",
        ],
        "next": ["nyx", "mode", "status", "work"],
    },
    "nyx": {
        "purpose": "Foreground Nyx directly; with prompt text, emit a Nyx-shaped interpretation payload and next commands.",
        "when_to_use": [
            "When you want a dedicated Nyx front door instead of `mode` or `run`.",
            "When you want terse symbolic or ambiguous text interpreted into bounded suggestions.",
        ],
        "examples": [
            "ygg nyx",
            "ygg nyx \"something chasing always\"",
            "ygg nyx --json \"audit the site routing\"",
        ],
        "next": ["suggest", "work", "mode"],
    },
    "heimdall": {
        "purpose": "Refresh Ygg's runtime embodiment snapshot and optionally write or route a continuity note.",
        "when_to_use": [
            "After host, model, session, or environment changes.",
            "When you want the runtime self snapshot updated under Ygg-owned state.",
        ],
        "examples": [
            "ygg heimdall --show-json",
            "ygg heimdall --note --ratatoskr",
        ],
        "next": ["ratatoskr", "status", "checkpoint"],
    },
    "ratatoskr": {
        "purpose": "Route structured continuity events into Ygg-owned note and promotion sinks.",
        "when_to_use": [
            "When you already have a structured event payload to route.",
            "When you want Ygg-local daily and promotion note surfaces instead of assistant-home defaults.",
        ],
        "examples": [
            "ygg ratatoskr --event-file /tmp/event.json",
            "ygg ratatoskr --event-json '{\"kind\":\"runtime-refresh\",\"route\":{\"daily\":true}}' --dry-run",
        ],
        "next": ["heimdall", "checkpoint", "promote"],
    },
}

VERB_CONTRACTS = {
    "suggest": {
        "mutates_state": False,
        "requires": ["request"],
        "optional": ["--domain", "--task", "--json"],
        "writes": [],
        "calls": ["tools.work_v1.router.classify_request", "tools.work_v1.planner.load_active_tasks"],
        "guarantees": [
            "never executes suggested commands",
            "prints a route interpretation with confidence and rationale",
            "returns at least one concrete ygg command suggestion",
        ],
        "fails_when": [
            "request is empty",
            "workspace planner/router imports are unavailable",
        ],
    },
    "work": {
        "mutates_state": "indirect",
        "requires": [],
        "optional": [
            "request...",
            "future target qualifiers",
            "future mode qualifiers",
        ],
        "writes": ["delegated to workspace work wrapper / planner session"],
        "calls": ["scripts/work.py"],
        "guarantees": [
            "currently forwards arguments verbatim to the workspace work wrapper",
            "target shape is a default human front door with deterministic continuity resolution under a soft NLP layer",
        ],
        "fails_when": ["workspace work script is missing or exits non-zero"],
    },
    "paths": {
        "mutates_state": False,
        "requires": [],
        "optional": ["show|check", "--paths-file", "--json"],
        "writes": [],
        "calls": ["path_contract.resolve_runtime_paths", "path_contract.validate_runtime_paths"],
        "guarantees": ["shows resolved paths and supports validation checks"],
        "fails_when": ["check mode returns non-zero when required paths are invalid"],
    },
    "bootstrap": {
        "mutates_state": False,
        "requires": ["inspect"],
        "optional": ["--profile", "--registry", "--json"],
        "writes": [],
        "calls": ["bootstrap_registry.resolve_registry_assignments", "bootstrap_registry.render_path_contract"],
        "guarantees": [
            "shows the resolved bootstrap profile and component graph",
            "shows package manifests and resolved Arch package list",
            "shows the rendered path-contract preview from the same registry source",
        ],
        "fails_when": [
            "profile file is missing",
            "component registry file is missing or invalid",
        ],
    },
    "inventory": {
        "mutates_state": False,
        "requires": [],
        "optional": ["--root", "--json"],
        "writes": [],
        "calls": ["inventory.build_repo_inventory"],
        "guarantees": [
            "reports implemented systems, bridges, state surfaces, speculative tracks, and next build targets",
            "never mutates repo or runtime state",
            "returns machine-readable JSON when requested",
        ],
        "fails_when": [
            "root path does not exist",
            "inventory root is not readable",
        ],
    },
    "root": {
        "mutates_state": "indirect",
        "requires": [],
        "optional": ["request...", "--session", "--openclaw-bin", "--print-packet"],
        "writes": ["planner message stream (unless --print-packet)"],
        "calls": ["tools.work_v1.planner.build_planner_boot_packet", "openclaw tui --session ... --message ..."],
        "guarantees": [
            "route action is forced to stay_in_planner",
            "does not auto-select branch/forge actions",
        ],
        "fails_when": [
            "workspace planner imports are unavailable",
            "OpenClaw TUI launch fails when not in --print-packet mode",
        ],
    },
    "branch": {
        "mutates_state": True,
        "requires": ["domain", "task"],
        "optional": [
            "--objective",
            "--current-state",
            "--next-action",
            "--status",
            "--priority",
            "--locked (repeatable)",
            "--rejected (repeatable)",
            "--reopen (repeatable)",
            "--artifact (repeatable)",
            "--agent",
            "--dry-run",
        ],
        "writes": ["workspace resume baton files via resume checkpoint"],
        "calls": ["scripts/resume.py checkpoint", "scripts/resume.py status"],
        "guarantees": [
            "normalizes domain/task ids to slug form",
            "prints the resulting domain status after successful checkpoint",
        ],
        "fails_when": ["resume checkpoint command exits non-zero"],
    },
    "resume": {
        "mutates_state": "indirect",
        "requires": [],
        "optional": ["domain", "task", "--semantic", "--max-chars", "--agent", "--openclaw-bin", "--print-only"],
        "writes": ["planner message stream when launching"],
        "calls": ["scripts/resume.py open"],
        "guarantees": [
            "resolves target from explicit args or sole active task",
            "supports print-only packet inspection",
        ],
        "fails_when": [
            "multiple active tasks exist and no explicit target is provided",
            "target resolution is ambiguous",
            "resume open command exits non-zero",
        ],
    },
    "forge": {
        "mutates_state": "indirect",
        "requires": [],
        "optional": ["request...", "--domain", "--task", "--session", "--openclaw-bin", "--print-packet", "--print-worker-command", "--wake-now", "--cwd"],
        "writes": ["planner message stream (unless --print-packet/--print-worker-command)"],
        "calls": ["tools.work_v1.planner.build_planner_boot_packet", "openclaw tui --session ... --message ...", "codex exec --full-auto ... (printed only when requested)"],
        "guarantees": [
            "route action is forced to suggest_spawn_codex",
            "target resolution requires an unambiguous active lane",
            "can print a ready worker command instead of launching planner when --print-worker-command is used",
            "can include an OpenClaw wake hook in the printed worker command when --wake-now is used",
            "remains an explicit lower-level execution control even if work becomes the default human entrypoint",
        ],
        "fails_when": [
            "no active task is available and no target is provided",
            "target resolution is ambiguous",
            "OpenClaw TUI launch fails when not in --print-packet mode",
        ],
    },
    "checkpoint": {
        "mutates_state": True,
        "requires": ["--lane", "--summary", "--disposition"],
        "optional": ["--promotion-target", "--evidence", "--next-action"],
        "writes": ["~/ygg/state/ygg/checkpoints/*.json"],
        "calls": ["continuity.write_checkpoint"],
        "guarantees": [
            "writes the Sandy Chaos continuity checkpoint shape into canonical Ygg control-plane state",
            "preserves disposition, evidence, next-action, and promotion-target fields",
        ],
        "fails_when": [
            "lane or summary is empty",
            "disposition is invalid",
            "promotion target is missing for a promotion disposition",
        ],
    },
    "promote": {
        "mutates_state": True,
        "requires": ["either domain+task+--disposition or --lane+--summary+--disposition"],
        "optional": [
            "--note",
            "--artifact (repeatable)",
            "--finish",
            "--dry-run",
            "--lane",
            "--summary",
            "--promotion-target",
            "--evidence",
            "--next-action",
        ],
        "writes": [
            "~/ygg/state/runtime/promotions.jsonl",
            "~/ygg/state/notes/promotions.md",
            "workspace resume baton (optional)",
            "~/ygg/state/ygg/checkpoints/*.json",
        ],
        "calls": ["scripts/resume.py checkpoint (log-daily)", "scripts/resume.py finish (--finish)", "continuity.write_checkpoint"],
        "guarantees": [
            "records explicit baton disposition events with timestamp",
            "supports SC-compatible promotion checkpoints",
            "supports dry-run without writing",
        ],
        "fails_when": [
            "disposition is omitted or invalid",
            "promotion target is missing for an SC promotion disposition",
            "follow-up resume checkpoint/finish command exits non-zero",
        ],
    },
    "status": {
        "mutates_state": False,
        "requires": [],
        "optional": ["domain", "--continuity"],
        "writes": [],
        "calls": ["scripts/resume.py status", "continuity.load_latest_checkpoint"],
        "guarantees": ["prints current domain/task baton summary or the latest continuity checkpoint"],
        "fails_when": ["resume status command exits non-zero"],
    },
    "raven": {
        "mutates_state": True,
        "requires": ["subcommand"],
        "optional": ["launch|status|inspect|return|adjudicate", "--json"],
        "writes": [
            "~/ygg/state/runtime/ravens/flights/*.json",
            "~/ygg/state/runtime/ravens/logs/*.jsonl",
            "~/ygg/state/runtime/ravens/returns/*.md",
        ],
        "calls": ["ravens_v1.launch_flight", "ravens_v1.list_flights", "ravens_v1.create_return_packet", "ravens_v1.adjudicate_flight"],
        "guarantees": [
            "flight launch records at least commissioned + launched events",
            "status/inspect expose persisted flight state",
            "return creates a structured markdown packet",
            "adjudicate records an explicit spine disposition on the flight",
        ],
        "fails_when": [
            "flight id is unknown for inspect/return/adjudicate",
            "return file exists and --force is not provided",
        ],
    },
    "graft": {
        "mutates_state": True,
        "requires": ["propose", "title"],
        "optional": ["--target-attachment", "--why-now", "--risk-class", "--source-flight", "--json"],
        "writes": ["~/ygg/state/runtime/ravens/grafts/GRAFT-*.md"],
        "calls": ["ravens_v1.propose_graft"],
        "guarantees": ["creates proposal artifact only (no automatic execution)"],
        "fails_when": ["proposal id exists and --force is not provided"],
    },
    "beak": {
        "mutates_state": True,
        "requires": ["propose", "title"],
        "optional": ["--class soft|hard", "--target", "--problem-type", "--evidence", "--json"],
        "writes": ["~/ygg/state/runtime/ravens/beaks/BEAK-*.md"],
        "calls": ["ravens_v1.propose_beak"],
        "guarantees": ["creates beak proposal artifact only (no destructive execution)"],
        "fails_when": ["proposal id exists and --force is not provided"],
    },
    "mode": {
        "mutates_state": True,
        "requires": ["nyx|solace|get|clear"],
        "optional": ["--session", "--openclaw-bin", "--print-message", "--no-notify", "--json"],
        "writes": [
            "~/ygg/state/runtime/persona-mode.json",
            "~/.openclaw/workspace-claw-main/state/persona-mode.json",
            "planner/session message stream (unless --no-notify or get)",
        ],
        "calls": ["openclaw tui --session ... --message ..."],
        "guarantees": [
            "persists current persona override state for future startup reads",
            "can notify a live session immediately with a mode directive",
            "get never mutates state",
            "clear returns control to automatic domain routing",
        ],
        "fails_when": [
            "OpenClaw session notification fails when notification is requested",
            "mode is outside nyx/solace/get/clear",
        ],
    },
    "run": {
        "mutates_state": True,
        "requires": ["nyx|solace|auto|get|clear"],
        "optional": ["--session", "--openclaw-bin", "--print-message", "--no-notify", "--json"],
        "writes": [
            "~/ygg/state/runtime/persona-mode.json",
            "~/.openclaw/workspace-claw-main/state/persona-mode.json",
            "planner/session message stream (unless --no-notify or get)",
        ],
        "calls": ["cmd_mode alias mapping"],
        "guarantees": [
            "supports `ygg run nyx` as a first-class alias",
            "maps auto to clear for a friendlier reset verb",
            "shares persistence and notification behavior with `ygg mode`",
        ],
        "fails_when": [
            "OpenClaw session notification fails when notification is requested",
            "action is outside nyx/solace/auto/get/clear",
        ],
    },
    "nyx": {
        "mutates_state": "sometimes",
        "requires": [],
        "optional": ["request...", "--session", "--openclaw-bin", "--notify", "--json"],
        "writes": [
            "~/ygg/state/runtime/persona-mode.json",
            "~/.openclaw/workspace-claw-main/state/persona-mode.json",
            "Nyx interpretation payload to stdout",
            "planner/session message stream (only when notifying or no request is provided)",
        ],
        "calls": ["cmd_mode", "tools.work_v1.router.classify_request", "tools.work_v1.planner.load_active_tasks"],
        "guarantees": [
            "`ygg nyx` foregrounds Nyx directly",
            "`ygg nyx <request>` emits a Nyx-shaped interpretation payload and suggestions",
            "references the nyx-nlp contract when present locally",
        ],
        "fails_when": [
            "workspace planner/router imports are unavailable for request interpretation",
            "OpenClaw session notification fails when notification is requested",
        ],
    },
    "heimdall": {
        "mutates_state": True,
        "requires": [],
        "optional": [
            "--workspace",
            "--state-file",
            "--daily-dir",
            "--dry-run",
            "--note",
            "--show-json",
            "--ratatoskr",
            "--timezone",
            "--channel",
            "--chat-type",
            "--runtime-core",
            "--session-key",
            "--openclaw-version",
            "--build",
            "--model",
            "--provider-auth",
            "--host-label",
            "--os-kernel",
            "--shell",
            "--node",
            "--reasoning",
            "--elevation",
        ],
        "writes": [
            "~/ygg/state/runtime/ygg-self.json",
            "~/ygg/state/notes/daily/*.md (when --note)",
        ],
        "calls": ["heimdall.build_runtime_snapshot", "ratatoskr.route_event (optional)"],
        "guarantees": [
            "updates Ygg-owned runtime embodiment state",
            "preserves runtime history with fingerprint tracking",
            "can hand meaningful changes to Ratatoskr instead of writing a direct note",
        ],
        "fails_when": [
            "state file path is not writable",
            "ratatoskr handoff payload is invalid",
        ],
    },
    "ratatoskr": {
        "mutates_state": True,
        "requires": ["--event-json or --event-file"],
        "optional": ["--workspace", "--daily-dir", "--promotion-file", "--dry-run", "--show-event"],
        "writes": [
            "~/ygg/state/notes/daily/*.md",
            "~/ygg/state/notes/promotion-candidates.md",
        ],
        "calls": ["ratatoskr.route_event"],
        "guarantees": [
            "routes structured continuity events into Ygg-owned sinks",
            "supports dry-run inspection without writes",
            "preserves event payload details in routed outputs",
        ],
        "fails_when": [
            "no event payload is provided",
            "event JSON cannot be parsed",
        ],
    },
}

MATCH_STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "into",
    "your",
    "my",
    "our",
    "just",
    "then",
    "work",
    "task",
    "project",
}


def _compact(text: str | None) -> str:
    return " ".join((text or "").split())


def _slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.strip().lower())
    return s.strip("-") or "untitled"


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _require_workspace_imports() -> None:
    if IMPORT_ERROR is not None:
        contract_hint = str(PATH_CONTRACT_FILE) if PATH_CONTRACT_FILE else "(not found; using fallback paths)"
        raise SystemExit(
            "Ygg could not import the current workspace implementation. "
            f"Expected modules under {WORKSPACE}. "
            f"Path contract source: {contract_hint}. "
            f"Original error: {IMPORT_ERROR}"
        )


def _run(cmd: list[str]) -> int:
    proc = subprocess.run(cmd)
    return int(proc.returncode)


def _render_cmd(cmd: list[str]) -> str:
    return shlex.join(cmd)


def _build_forge_worker_command(
    *,
    domain: str,
    task: str,
    request: str,
    cwd: str | None,
    openclaw_bin: str,
    wake_now: bool,
) -> str:
    lane = f"{domain}/{task}"
    prompt_lines = [
        f"Continue the {lane} lane.",
        "",
        "Task:",
        request,
        "",
        "Constraints:",
        "- keep scope tight",
        "- run relevant tests",
        "- do not commit unless asked",
    ]
    if wake_now:
        notify_cmd = _render_cmd(
            [
                openclaw_bin,
                "system",
                "event",
                "--text",
                f"Done: {lane}; summarize changes, validation status, and next step",
                "--mode",
                "now",
            ]
        )
        prompt_lines.extend(
            [
                "",
                "When completely finished, run this command to notify me:",
                notify_cmd,
            ]
        )

    cmd = ["codex"]
    worker_cwd = _compact(cwd) or os.getcwd()
    if worker_cwd:
        cmd.extend(["-C", worker_cwd])
    cmd.extend(["exec", "--full-auto", "\n".join(prompt_lines)])
    return _render_cmd(cmd)


def _active_tasks():
    _require_workspace_imports()
    return load_active_tasks(WORKSPACE)


def _active_task_rows(tasks) -> list[dict[str, str]]:
    return [
        {
            "domain": t.domain,
            "task": t.task,
            "status": t.status,
            "freshness": t.freshness,
            "objective": t.objective,
            "next_action": t.next_action,
        }
        for t in tasks
    ]


def _looks_like_continue(text: str) -> bool:
    text = _compact(text).lower()
    return any(phrase in text for phrase in ["resume", "continue", "pick back up", "where we left off", "continue where"])


def _looks_like_impl(text: str) -> bool:
    text = _compact(text).lower()
    return any(phrase in text for phrase in ["implement", "build", "fix", "code", "wire up"])


def _match_tokens(text: str) -> set[str]:
    tokens = set(re.findall(r"[a-z0-9]{3,}", text.lower()))
    return {tok for tok in tokens if tok not in MATCH_STOPWORDS}


def _infer_task_from_request(request: str, tasks):
    request_tokens = _match_tokens(request)
    if not request_tokens:
        return None

    scored: list[tuple[int, object]] = []
    for task in tasks:
        id_tokens = _match_tokens(f"{task.domain} {task.task}")
        desc_tokens = _match_tokens(f"{task.objective} {task.next_action}")
        score = 2 * len(request_tokens & id_tokens) + len(request_tokens & desc_tokens)
        if score > 0:
            scored.append((score, task))

    if not scored:
        return None

    scored.sort(key=lambda item: item[0], reverse=True)
    top_score, top_task = scored[0]
    second_score = scored[1][0] if len(scored) > 1 else -1
    if top_score >= 2 and top_score > second_score:
        return top_task
    return None


def _resolve_target(domain: str | None, task: str | None, *, require_task: bool, verb: str) -> tuple[str, str | None]:
    tasks = _active_tasks()

    if task and not domain:
        raise SystemExit(f"`ygg {verb}` requires a domain when task is provided.")

    if domain and task:
        return _slugify(domain), _slugify(task)

    if domain and not task:
        domain_slug = _slugify(domain)
        matches = [t for t in tasks if t.domain == domain_slug]
        if require_task and len(matches) == 1:
            return matches[0].domain, matches[0].task
        if require_task and len(matches) != 1:
            if not matches:
                raise SystemExit(
                    f"`ygg {verb}` needs a concrete task for domain `{domain_slug}`. "
                    "No active task was found for that domain."
                )
            raise SystemExit(
                f"`ygg {verb}` found multiple active matches for domain `{domain_slug}`; "
                "please specify a task explicitly."
            )
        return domain_slug, None

    if not tasks:
        raise SystemExit("No active tasks tracked yet. Create one with `ygg branch ...` first.")

    if len(tasks) == 1:
        only = tasks[0]
        return only.domain, only.task if require_task else only.task

    choices = "\n".join(f"- {t.domain} / {t.task} [{t.status}, {t.freshness}]" for t in tasks)
    raise SystemExit(
        f"`ygg {verb}` needs an explicit target because multiple active tasks exist:\n{choices}"
    )


def _launch_packet(packet: str, *, session: str, openclaw_bin: str, print_packet: bool) -> int:
    if print_packet:
        print(packet, end="")
        return 0
    return _run([openclaw_bin, "tui", "--session", session, "--message", packet])


def _forced_packet(*, request: str | None, action: str, reason: str, session: str, needs_approval: bool, domain: str | None = None, task: str | None = None, confidence: float = 0.95) -> str:
    _require_workspace_imports()
    route = RouteSuggestion(
        action=action,
        confidence=confidence,
        reason=reason,
        needs_approval=needs_approval,
        domain=domain,
        task=task,
    )
    return build_planner_boot_packet(
        workspace=WORKSPACE,
        request=_compact(request) or None,
        route=route,
        planner_session_suffix=session,
    )


def _load_mode_state() -> dict[str, object]:
    if PERSONA_MODE_FILE.exists():
        try:
            payload = json.loads(PERSONA_MODE_FILE.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            pass
    return {
        "defaultMode": "auto",
        "overrideMode": None,
        "effectiveMode": "auto",
        "updatedAt": None,
        "source": "ygg-mode",
    }


def _save_mode_state(payload: dict[str, object]) -> None:
    for file_path in (PERSONA_MODE_FILE, WORKSPACE_PERSONA_MODE_FILE):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _mode_message(override: str | None) -> str:
    if override == "nyx":
        return (
            "Mode directive: switch foreground persona to Nyx until further notice. "
            "Nyx is the interpretive lead now, especially for architecture, failure analysis, and naming. "
            "If Ian asks for plain speech or practical sequencing, collapse cleanly into Solace-style clarity as needed."
        )
    if override == "solace":
        return (
            "Mode directive: switch foreground persona to Solace until further notice. "
            "Lead with grounded, practical, stabilizing responses unless Ian explicitly requests Nyx or a shadow read."
        )
    return (
        "Mode directive cleared: return to automatic persona routing. "
        "Use Nyx by default for architecture, failure analysis, and naming; use Solace elsewhere unless Ian explicitly asks otherwise."
    )


def _print_mode_text(payload: dict[str, object]) -> None:
    print("Ygg mode\n")
    print(f"- default: {payload.get('defaultMode', 'auto')}")
    print(f"- override: {payload.get('overrideMode') or 'none'}")
    print(f"- effective: {payload.get('effectiveMode', 'auto')}")
    if payload.get('updatedAt'):
        print(f"- updated: {payload['updatedAt']}")
    if payload.get('workspaceFile'):
        print(f"- workspace file: {payload['workspaceFile']}")
    if payload.get('yggFile'):
        print(f"- ygg file: {payload['yggFile']}")
    if payload.get('notify') is not None:
        print(f"- notify: {'yes' if payload.get('notify') else 'no'}")
    if payload.get('session'):
        print(f"- session: {payload['session']}")
    if payload.get('message'):
        print("\nmessage:")
        print(payload['message'])


def _append_promotion_record(record: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    with PROMOTION_LOG_JSONL.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    lines = [
        f"## {record['timestamp']} — {record['domain']} / {record['task']}",
        f"- disposition: {record['disposition']}",
        f"- finish: {'yes' if record['finish'] else 'no'}",
    ]
    note = _compact(record.get("note"))
    if note:
        lines.append(f"- note: {note}")
    artifacts = record.get("artifacts") or []
    if artifacts:
        lines.append("- artifacts:")
        lines.extend(f"  - {artifact}" for artifact in artifacts)
    lines.append("")

    with PROMOTION_LOG_MD.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def _quoted_command(parts: list[str], text: str | None = None) -> str:
    cmd = list(parts)
    text = _compact(text)
    if text:
        cmd.append(text)
    return _render_cmd(cmd)


def _resolve_suggest_target(route, tasks, domain_hint: str | None, task_hint: str | None) -> tuple[str | None, str | None]:
    domain = _slugify(domain_hint) if domain_hint else route.domain
    task = _slugify(task_hint) if task_hint else route.task

    if domain and not task:
        matches = [t for t in tasks if t.domain == domain]
        if len(matches) == 1:
            task = matches[0].task

    return domain, task


def _augment_route_for_suggest(route, request: str, tasks, *, domain_hint: str | None = None, task_hint: str | None = None):
    hinted_domain = _slugify(domain_hint) if domain_hint else None
    hinted_task = _slugify(task_hint) if task_hint else None
    inferred = _infer_task_from_request(request, tasks)

    # Preserve explicit create-task requests.
    if route.action == "suggest_create_task":
        return route

    # If the router already chose a lane-oriented action, fill any missing target from hints/inference.
    if route.action in {"suggest_resume_active_task", "suggest_spawn_codex"}:
        domain = route.domain or hinted_domain or (inferred.domain if inferred else None)
        task = route.task or hinted_task or (inferred.task if inferred else None)
        if domain or task:
            return RouteSuggestion(
                action=route.action,
                confidence=route.confidence,
                reason=route.reason,
                needs_approval=route.needs_approval,
                domain=domain,
                task=task,
            )
        return route

    if hinted_domain and hinted_task:
        if _looks_like_impl(request):
            return RouteSuggestion(
                action="suggest_spawn_codex",
                confidence=max(route.confidence, 0.82),
                reason="Suggest-layer target hints plus implementation-shaped language.",
                needs_approval=False,
                domain=hinted_domain,
                task=hinted_task,
            )
        if _looks_like_continue(request):
            return RouteSuggestion(
                action="suggest_resume_active_task",
                confidence=max(route.confidence, 0.82),
                reason="Suggest-layer target hints plus continuation-shaped language.",
                needs_approval=False,
                domain=hinted_domain,
                task=hinted_task,
            )
        return RouteSuggestion(
            action=route.action,
            confidence=route.confidence,
            reason=route.reason,
            needs_approval=route.needs_approval,
            domain=hinted_domain,
            task=hinted_task,
        )

    if inferred and route.action in {"stay_in_planner", "ask_for_clarification"}:
        if _looks_like_impl(request):
            return RouteSuggestion(
                action="suggest_spawn_codex",
                confidence=max(route.confidence, 0.74),
                reason="Suggest-layer overlap with an active lane plus implementation-shaped language.",
                needs_approval=False,
                domain=inferred.domain,
                task=inferred.task,
            )
        if _looks_like_continue(request):
            return RouteSuggestion(
                action="suggest_resume_active_task",
                confidence=max(route.confidence, 0.76),
                reason="Suggest-layer overlap with an active lane plus continuation-shaped language.",
                needs_approval=False,
                domain=inferred.domain,
                task=inferred.task,
            )
        return RouteSuggestion(
            action=route.action,
            confidence=route.confidence,
            reason=f"{route.reason} Suggest layer also found a likely target.",
            needs_approval=route.needs_approval,
            domain=inferred.domain,
            task=inferred.task,
        )

    return route


def _branch_template(request: str, domain_hint: str | None, task_hint: str | None) -> tuple[str, bool]:
    objective = _compact(request)
    if domain_hint and task_hint:
        command = _render_cmd(
            [
                "ygg",
                "branch",
                _slugify(domain_hint),
                _slugify(task_hint),
                "--objective",
                objective,
                "--next-action",
                "Clarify scope and begin execution.",
            ]
        )
        return command, True

    domain_part = _slugify(domain_hint) if domain_hint else "<domain>"
    task_part = _slugify(task_hint) if task_hint else "<task>"
    command = f"ygg branch {domain_part} {task_part} --objective {shlex.quote(objective)}"
    return command, False


def _suggestion_entry(command: str, why: str, *, primary: bool = False, executable: bool = True) -> dict[str, object]:
    verb = command.split()[1] if command.startswith("ygg ") and len(command.split()) > 1 else ""
    return {
        "command": command,
        "why": why,
        "primary": primary,
        "executable": executable,
        "verb": verb,
        "blurb": SUGGESTION_BLURBS.get(verb, ""),
        "contract_ref": f"ygg help {verb}" if verb in EXPLAIN_CARDS else None,
    }


def _build_suggestions(request: str, route, tasks, *, domain_hint: str | None = None, task_hint: str | None = None) -> list[dict[str, object]]:
    request = _compact(request)
    target_domain, target_task = _resolve_suggest_target(route, tasks, domain_hint, task_hint)
    suggestions: list[dict[str, object]] = []
    seen: set[str] = set()

    def add(command: str, why: str, *, primary: bool = False, executable: bool = True) -> None:
        if command in seen:
            return
        seen.add(command)
        suggestions.append(_suggestion_entry(command, why, primary=primary, executable=executable))

    branch_cmd, branch_executable = _branch_template(request, domain_hint, task_hint)

    if route.action == "suggest_resume_active_task":
        if target_domain and target_task:
            add(
                _render_cmd(["ygg", "resume", target_domain, target_task]),
                "Best fit when the request looks like continuation work.",
                primary=True,
            )
            add(
                _quoted_command(["ygg", "forge", "--domain", target_domain, "--task", target_task], request),
                "Use this if you want implementation/delegation immediately after resuming the lane mentally.",
            )
        add(_quoted_command(["ygg", "root"], request), "Stay in the planner if you want to think before acting.")
        add("ygg status", "Inspect active lanes before choosing.")

    elif route.action == "suggest_spawn_codex":
        if target_domain and target_task:
            add(
                _quoted_command(["ygg", "forge", "--domain", target_domain, "--task", target_task], request),
                "Best fit when the request is implementation-shaped and already points at an active lane.",
                primary=True,
            )
            add(
                _render_cmd(["ygg", "resume", target_domain, target_task]),
                "Reopen the lane first if you want the baton context before implementation.",
            )
        else:
            add(_quoted_command(["ygg", "work"], request), "Let the planner disambiguate the implementation target.", primary=True)
        add(_quoted_command(["ygg", "root"], request), "Keep the decision in the planner if you are not ready to bias toward execution.")
        add("ygg status", "Inspect active lanes before choosing.")

    elif route.action == "suggest_create_task":
        add(
            branch_cmd,
            "Best fit when the request clearly sounds like separate work that should become its own lane.",
            primary=True,
            executable=branch_executable,
        )
        add(_quoted_command(["ygg", "root"], request), "Stay in the planner if you want help naming the lane before creating it.")
        add(_quoted_command(["ygg", "work"], request), "Use the flexible front door if you want planner oversight over branch creation.")
        add("ygg status", "Inspect the current lane map before branching.")

    elif route.action == "ask_for_clarification":
        add("ygg status", "Best fit when multiple active lanes exist and the request is ambiguous.", primary=True)
        add(_quoted_command(["ygg", "root"], request), "Use the planner to resolve ambiguity explicitly.")
        add(
            branch_cmd,
            "Use this only if you already know the work should become a separate lane.",
            executable=branch_executable,
        )

    else:  # stay_in_planner or unknown future actions
        add(_quoted_command(["ygg", "work"], request), "Best fit when the route is unclear and planner oversight is desirable.", primary=True)
        add(_quoted_command(["ygg", "root"], request), "Use this if you want to stay in the spine without route inference pressure.")
        if target_domain and target_task:
            add(_render_cmd(["ygg", "resume", target_domain, target_task]), "This looks viable because the request overlaps an active lane.")
        add("ygg status", "Inspect active lanes before choosing.")

    return suggestions


def _print_suggest_text(payload: dict[str, object]) -> None:
    route = payload["route"]
    suggestions = payload["suggestions"]
    active_tasks = payload["active_tasks"]

    print("Ygg suggest\n")
    print(f"request: {payload['request']}")
    print("\nroute interpretation:")
    print(f"- action: {route['action']}")
    print(f"- confidence: {route['confidence']:.2f}")
    print(f"- needsApproval: {'yes' if route['needs_approval'] else 'no'}")
    print(f"- reason: {route['reason']}")
    if route.get("domain") or route.get("task"):
        print(f"- target: {route.get('domain') or '?'} / {route.get('task') or '?'}")

    primary = next((item for item in suggestions if item.get("primary")), None)
    alternatives = [item for item in suggestions if not item.get("primary")]

    if primary:
        print("\nprimary suggestion:")
        print(f"1. {primary['command']}")
        print(f"   why: {primary['why']}")
        if primary.get("blurb"):
            print(f"   posture: {primary['blurb']}")
        if primary.get("contract_ref"):
            print(f"   contract: {primary['contract_ref']}")
        if not primary.get("executable", True):
            print("   note: template command — fill in the placeholder values first.")

    if alternatives:
        print("\nother good options:")
        for idx, item in enumerate(alternatives, start=2 if primary else 1):
            print(f"{idx}. {item['command']}")
            print(f"   why: {item['why']}")
            if item.get("blurb"):
                print(f"   posture: {item['blurb']}")
            if item.get("contract_ref"):
                print(f"   contract: {item['contract_ref']}")
            if not item.get("executable", True):
                print("   note: template command — fill in the placeholder values first.")

    if active_tasks:
        print("\nactive tasks:")
        for row in active_tasks:
            print(
                f"- {row['domain']} / {row['task']} [{row['status']}, {row['freshness']}] "
                f"— next: {row['next_action']}"
            )


def _print_explain_card(verb: str, card: dict[str, object], contract: dict[str, object], *, invoked_as: str = "explain") -> None:
    print(f"ygg {invoked_as} {verb}\n")
    print(f"purpose: {card['purpose']}")

    when_to_use = card.get("when_to_use") or []
    if when_to_use:
        print("\nwhen to use:")
        for item in when_to_use:
            print(f"- {item}")

    print("\ncontract:")
    print(f"- mutates state: {contract.get('mutates_state')}")

    requires = contract.get("requires") or []
    if requires:
        print("- required inputs:")
        for item in requires:
            print(f"  - {item}")

    optional = contract.get("optional") or []
    if optional:
        print("- optional flags/inputs:")
        for item in optional:
            print(f"  - {item}")

    guarantees = contract.get("guarantees") or []
    if guarantees:
        print("- guarantees:")
        for item in guarantees:
            print(f"  - {item}")

    fails_when = contract.get("fails_when") or []
    if fails_when:
        print("- fails when:")
        for item in fails_when:
            print(f"  - {item}")

    examples = card.get("examples") or []
    if examples:
        print("\nexamples:")
        for ex in examples:
            print(f"- {ex}")

    next_verbs = card.get("next") or []
    if next_verbs:
        print("\nlikely next verbs:")
        print("- " + ", ".join(f"ygg {v}" for v in next_verbs))


def cmd_explain(args: argparse.Namespace) -> int:
    invoked_as = getattr(args, "invoked_as", "explain")
    if not args.verb:
        verbs = sorted(EXPLAIN_CARDS.keys())
        payload = {
            "verbs": [
                {
                    "verb": v,
                    "purpose": EXPLAIN_CARDS[v]["purpose"],
                    "mutates_state": VERB_CONTRACTS.get(v, {}).get("mutates_state"),
                }
                for v in verbs
            ],
            "hint": f"Run `ygg {invoked_as} <verb>` for details.",
        }
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            return 0

        print(f"Ygg {invoked_as}\n")
        print("known verbs:")
        for v in verbs:
            mutates = VERB_CONTRACTS.get(v, {}).get("mutates_state")
            print(f"- {v}: {EXPLAIN_CARDS[v]['purpose']} (mutates_state={mutates})")
        print(f"\nRun `ygg {invoked_as} <verb>` for full details.")
        return 0

    verb = _slugify(args.verb)
    card = EXPLAIN_CARDS.get(verb)
    if not card:
        known = ", ".join(sorted(EXPLAIN_CARDS.keys()))
        raise SystemExit(f"Unknown verb `{verb}`. Known verbs: {known}")

    payload = {
        "verb": verb,
        **card,
        "contract": VERB_CONTRACTS.get(verb, {}),
    }
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    _print_explain_card(verb, card, VERB_CONTRACTS.get(verb, {}), invoked_as=invoked_as)
    return 0


def cmd_suggest(args: argparse.Namespace) -> int:
    _require_workspace_imports()
    request = _compact(" ".join(args.request))
    if not request:
        raise SystemExit("`ygg suggest` needs a natural-language request.")

    tasks = _active_tasks()
    route = classify_request(request, tasks)
    route = _augment_route_for_suggest(
        route,
        request,
        tasks,
        domain_hint=args.domain,
        task_hint=args.task,
    )
    suggestions = _build_suggestions(
        request,
        route,
        tasks,
        domain_hint=args.domain,
        task_hint=args.task,
    )
    payload = {
        "request": request,
        "route": {
            "action": route.action,
            "confidence": route.confidence,
            "reason": route.reason,
            "needs_approval": route.needs_approval,
            "domain": route.domain,
            "task": route.task,
        },
        "hints": {
            "domain": _slugify(args.domain) if args.domain else None,
            "task": _slugify(args.task) if args.task else None,
        },
        "suggestions": suggestions,
        "active_tasks": _active_task_rows(tasks),
    }

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    _print_suggest_text(payload)
    return 0


def _apply_mode_action(action: str, *, session: str, openclaw_bin: str, no_notify: bool) -> tuple[dict[str, object], int]:
    state = _load_mode_state()

    if action == "get":
        payload = dict(state)
        payload.update({
            "action": "get",
            "workspaceFile": str(WORKSPACE_PERSONA_MODE_FILE),
            "yggFile": str(PERSONA_MODE_FILE),
        })
        return payload, 0

    override = None if action == "clear" else action
    payload = {
        "defaultMode": "auto",
        "overrideMode": override,
        "effectiveMode": override or "auto",
        "updatedAt": _now_iso(),
        "source": "ygg-mode",
        "workspaceFile": str(WORKSPACE_PERSONA_MODE_FILE),
        "yggFile": str(PERSONA_MODE_FILE),
        "notify": not no_notify,
        "session": None if no_notify else session,
    }
    message = _mode_message(override)
    payload["message"] = message

    _save_mode_state(payload)

    rc = 0
    if not no_notify:
        rc = _run([openclaw_bin, "tui", "--session", session, "--message", message])
        if rc != 0:
            payload["notified"] = False
            payload["notifyExit"] = rc
            return payload, rc

    payload["notified"] = not no_notify
    return payload, 0


def cmd_mode(args: argparse.Namespace) -> int:
    action = args.action.lower()
    payload, rc = _apply_mode_action(action, session=args.session, openclaw_bin=args.openclaw_bin, no_notify=args.no_notify)

    if args.print_message:
        print(payload.get("message", ""))
        return 0

    if rc != 0:
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            _print_mode_text(payload)
            print(f"\nwarning: mode persisted, but live session notification failed (exit {rc}).")
        return rc

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _print_mode_text(payload)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    action = args.action.lower()
    mapped = "clear" if action == "auto" else action
    alias_args = argparse.Namespace(**vars(args))
    alias_args.action = mapped
    return cmd_mode(alias_args)


def _nyx_contract_ref() -> dict[str, str] | None:
    local_schema = HOME / "projects" / "nyx-nlp" / "schemas" / "intent.schema.json"
    if local_schema.exists():
        return {
            "path": str(local_schema),
            "url": "https://github.com/yanmo42/nyx-nlp/blob/main/schemas/intent.schema.json",
        }
    return {
        "url": "https://github.com/yanmo42/nyx-nlp/blob/main/schemas/intent.schema.json",
    }


def _confidence_band(c: float) -> str:
    if c >= 0.85:
        return "high"
    if c >= 0.65:
        return "medium"
    return "low"


def _print_nyx_text(payload: dict[str, object]) -> None:
    print("Ygg nyx\n")
    print(f"request:    {payload['request']}")
    print(f"intent:     {payload['intent']}")
    print(f"route:      {payload['route']}")

    conf = float(payload["confidence"])
    band = _confidence_band(conf)
    flag = "  !" if band == "low" else ""
    print(f"confidence: {conf:.2f}  ({band}){flag}")

    reason = payload.get("reason")
    if reason:
        print(f"reason:     {reason}")

    active_tasks = payload.get("active_tasks") or []
    if active_tasks:
        print(f"\nactive tasks ({len(active_tasks)}):")
        for row in active_tasks:
            freshness = row.get("freshness", "")
            flag = "  !" if freshness == "stale" else ""
            print(f"  [{row.get('domain')}] {row.get('task')}  {freshness}{flag}")
            if row.get("next_action"):
                print(f"    → {row['next_action']}")

    ambiguities = payload.get("ambiguities") or []
    if ambiguities:
        print("\nambiguities:")
        for item in ambiguities:
            print(f"  ! {item}")

    notes = payload.get("notes") or []
    if notes:
        print("\nnotes:")
        for item in notes:
            print(f"  - {item}")

    suggestions = payload.get("suggestions") or []
    if suggestions:
        print("\nnext:")
        for idx, entry in enumerate(suggestions, start=1):
            star = " *" if entry.get("primary") else ""
            print(f"  {idx}. {entry['command']}{star}")
            why = entry.get("why")
            if why:
                print(f"     {why}")


def cmd_nyx(args: argparse.Namespace) -> int:
    request = _compact(" ".join(args.request))
    notify = getattr(args, "notify", False)

    mode_payload, rc = _apply_mode_action("nyx", session=args.session, openclaw_bin=args.openclaw_bin, no_notify=not notify)
    if rc != 0:
        if args.json:
            print(json.dumps(mode_payload, indent=2, ensure_ascii=False))
        else:
            _print_mode_text(mode_payload)
            print(f"\nwarning: mode persisted, but live session notification failed (exit {rc}).")
        return rc

    if not request:
        if args.json:
            print(json.dumps(mode_payload, indent=2, ensure_ascii=False))
        else:
            _print_mode_text(mode_payload)
        return 0

    _require_workspace_imports()
    tasks = _active_tasks()
    route = classify_request(request, tasks)
    route = _augment_route_for_suggest(route, request, tasks)
    suggestions = _build_suggestions(request, route, tasks)
    ambiguities: list[str] = []
    notes = [
        "foreground mode forced to nyx",
        "Nyx request interpretation leaves tracks before execution",
    ]
    if route.action == "ask_for_clarification":
        ambiguities.append("request remains ambiguous after first-pass routing")
    if route.needs_approval:
        notes.append("suggested follow-up may require approval")

    payload = {
        "request": request,
        "intent": route.action,
        "confidence": route.confidence,
        "mode": "nyx",
        "route": suggestions[0]["verb"] if suggestions else route.action,
        "notes": notes,
        "ambiguities": ambiguities,
        "contract": _nyx_contract_ref(),
        "reason": route.reason,
        "suggestions": suggestions,
        "active_tasks": _active_task_rows(tasks),
    }
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    _print_nyx_text(payload)
    return 0


def cmd_work(args: argparse.Namespace) -> int:
    cmd = [sys.executable, str(WORK_SCRIPT)]
    if PATH_CONTRACT_FILE is not None:
        cmd.extend(["--paths-file", str(PATH_CONTRACT_FILE)])
    cmd.extend(args.request)
    return _run(cmd)


def cmd_root(args: argparse.Namespace) -> int:
    request = _compact(" ".join(args.request)) or None
    packet = _forced_packet(
        request=request,
        action="stay_in_planner",
        reason="Forced planner entry via ygg root.",
        session=args.session,
        needs_approval=False,
        confidence=1.0 if not request else 0.98,
    )
    return _launch_packet(packet, session=args.session, openclaw_bin=args.openclaw_bin, print_packet=args.print_packet)


def _continuity_payload() -> dict[str, object]:
    checkpoint = load_latest_checkpoint(YGG_HOME)
    if checkpoint is None:
        return {"status": "empty", "message": "no Ygg checkpoints yet"}
    return checkpoint.to_dict()


def _write_continuity_from_args(args: argparse.Namespace) -> Path:
    return write_continuity_checkpoint(
        YGG_HOME,
        lane=args.lane,
        summary=args.summary,
        disposition=args.disposition,
        promotion_target=args.promotion_target,
        evidence=args.evidence,
        next_action=args.next_action,
    )


def _is_continuity_promote(args: argparse.Namespace) -> bool:
    return bool(args.lane or args.summary or args.promotion_target or args.evidence or args.next_action)


def cmd_checkpoint(args: argparse.Namespace) -> int:
    try:
        path = _write_continuity_from_args(args)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    print(json.dumps({"status": "ok", "checkpoint": str(path.relative_to(YGG_HOME))}, indent=2, ensure_ascii=False))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    if args.continuity:
        print(json.dumps(_continuity_payload(), indent=2, ensure_ascii=False))
        return 0
    cmd = [sys.executable, str(RESUME_SCRIPT), "status"]
    if args.domain:
        cmd.append(_slugify(args.domain))
    return _run(cmd)


def _print_paths_text(payload: dict[str, object], check: dict[str, object] | None = None) -> None:
    contract = payload["contract"]
    resolved = payload["resolved"]

    print("Ygg path contract\n")
    print(f"contract loaded: {'yes' if contract.get('loaded') else 'no'}")
    print(f"contract path: {contract.get('path')}")

    parse_error = contract.get("parse_error")
    if parse_error:
        print(f"parse error: {parse_error}")

    print("\nresolved paths:")
    print(f"- spine root: {resolved.get('spine_root')}")
    print(f"- control plane root: {resolved.get('control_plane_root')}")
    print(f"- control plane bin: {resolved.get('control_plane_bin')}")
    print(f"- work repos root: {resolved.get('work_repos_root')}")

    if check is not None:
        print(f"\ncheck: {'ok' if check.get('ok') else 'failed'}")
        errors = check.get("errors") or []
        warnings = check.get("warnings") or []
        if errors:
            print("errors:")
            for item in errors:
                print(f"- {item}")
        if warnings:
            print("warnings:")
            for item in warnings:
                print(f"- {item}")


def cmd_paths(args: argparse.Namespace) -> int:
    runtime = resolve_runtime_paths(args.paths_file)
    payload = runtime_payload(runtime)

    if args.action == "show":
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            return 0
        _print_paths_text(payload)
        return 0

    check = validate_runtime_paths(runtime)
    payload["check"] = check
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _print_paths_text(payload, check=check)
    return 0 if check.get("ok") else 1


def _resolve_profile_file(profile: str) -> Path:
    requested = (profile or DEFAULT_BOOTSTRAP_PROFILE).strip()
    if "/" in requested or requested.startswith("."):
        return Path(requested).expanduser().resolve()
    return (PROFILE_DIR / f"bootstrap-profile.{requested}.env").resolve()


def _resolve_asset_path(raw: str) -> Path:
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (YGG_HOME / path).resolve()


def _bootstrap_payload(profile: str, registry: Path) -> dict[str, object]:
    profile_file = _resolve_profile_file(profile)
    if not profile_file.exists():
        raise SystemExit(f"Bootstrap profile not found: {profile_file}")
    if not registry.exists():
        raise SystemExit(f"Component registry not found: {registry}")

    profile_env = parse_profile_env(profile_file)
    resolved_env = {**profile_env, **os.environ}
    assignments = resolve_registry_assignments(registry, profile=profile, env=resolved_env)
    registry_data = load_registry(registry)
    components_cfg = registry_data.get("components", {})

    manifests_raw = resolved_env.get("PACMAN_PACKAGE_MANIFESTS", "state/profiles/arch-packages.base.txt")
    manifest_paths = [_resolve_asset_path(item) for item in manifests_raw.split(":") if item.strip()]
    packages: list[str] = []
    seen: set[str] = set()
    for manifest_path in manifest_paths:
        for package in read_package_manifest(manifest_path):
            if package in seen:
                continue
            seen.add(package)
            packages.append(package)

    component_rows: list[dict[str, object]] = []
    if isinstance(components_cfg, dict):
        for component_id, component in components_cfg.items():
            if not isinstance(component, dict):
                continue
            component_rows.append(
                {
                    "id": str(component_id),
                    "label": component.get("label", component_id),
                    "root": assignments.get(str(component.get("env_root", "")).strip(), ""),
                    "url": assignments.get(str(component.get("env_url", "")).strip(), ""),
                    "ref": assignments.get(str(component.get("env_ref", "")).strip(), ""),
                    "enabled": assignments.get(str(component.get("env_enabled", "")).strip(), "0") == "1",
                }
            )

    workspace_root = assignments.get("WORKSPACE_ROOT") or str(WORKSPACE)
    contract_path = str(Path(workspace_root).expanduser() / "config" / "ygg-paths.yaml")
    path_contract_preview = render_path_contract(
        registry,
        profile=profile,
        contract_path=contract_path,
        env=resolved_env,
    )

    return {
        "profile": {"name": profile, "file": str(profile_file)},
        "registry": {
            "path": str(registry),
            "schema": assignments.get("COMPONENT_REGISTRY_SCHEMA", ""),
        },
        "manifests": [str(path) for path in manifest_paths],
        "packages": packages,
        "components": component_rows,
        "assignments": assignments,
        "path_contract_preview": path_contract_preview,
    }


def _print_bootstrap_text(payload: dict[str, object]) -> None:
    profile = payload["profile"]
    registry = payload["registry"]

    print("Ygg bootstrap inspect\n")
    print(f"profile: {profile['name']}")
    print(f"profile file: {profile['file']}")
    print(f"registry: {registry['path']}")
    print(f"registry schema: {registry['schema']}")

    manifests = payload.get("manifests") or []
    if manifests:
        print("\npackage manifests:")
        for path in manifests:
            print(f"- {path}")

    packages = payload.get("packages") or []
    if packages:
        print(f"\npackages ({len(packages)}):")
        print("- " + ", ".join(packages))

    components = payload.get("components") or []
    if components:
        print("\ncomponents:")
        for row in components:
            enabled = "enabled" if row.get("enabled") else "disabled"
            print(
                f"- {row.get('id')} [{enabled}] root={row.get('root')} ref={row.get('ref') or '(none)'}"
            )
            if row.get("url"):
                print(f"  url: {row['url']}")

    preview = str(payload.get("path_contract_preview", "")).rstrip()
    if preview:
        print("\npath contract preview:")
        print(preview)


def cmd_bootstrap_inspect(args: argparse.Namespace) -> int:
    profile = args.profile or DEFAULT_BOOTSTRAP_PROFILE
    registry = _resolve_asset_path(args.registry)
    payload = _bootstrap_payload(profile, registry)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0
    _print_bootstrap_text(payload)
    return 0


def _print_inventory_text(payload: dict[str, object]) -> None:
    summary = payload["summary"]
    print("Ygg inventory\n")
    print(f"root: {payload['root']}")
    print(
        "summary: "
        f"implemented={summary['implementedCount']} "
        f"partial={summary['partialCount']} "
        f"speculative={summary['speculativeCount']} "
        f"bridges={summary['bridgeCount']} "
        f"programs={summary['programCount']} "
        f"ideas={summary['ideaCount']}"
    )

    systems = payload.get("systems") or []
    if systems:
        print("\nimplemented / partial systems:")
        for row in systems:
            commands = ", ".join(row.get("commands") or []) or "(none)"
            print(f"- [{row['status']}] {row['title']} ({row['id']})")
            print(f"  {row['summary']}")
            print(f"  commands: {commands}")

    bridges = payload.get("bridges") or []
    if bridges:
        print("\nbridge surfaces:")
        for row in bridges:
            print(f"- {row['relativePath']} [{row['kind']}]")
            if row.get("reason"):
                print(f"  {row['reason']}")

    state_surfaces = payload.get("stateSurfaces") or []
    if state_surfaces:
        print("\nstate surfaces:")
        for row in state_surfaces:
            print(f"- {row['relativePath']} [{row['kind']}]")
            if row.get("reason"):
                print(f"  {row['reason']}")

    speculative = payload.get("speculativeTracks") or []
    if speculative:
        print("\nspeculative tracks:")
        for row in speculative:
            print(f"- {row['title']} ({row['id']})")
            print(f"  {row['summary']}")

    next_targets = payload.get("nextTargets") or []
    if next_targets:
        print("\nnext targets:")
        for row in next_targets:
            print(f"- [{row['priority']}] {row['title']} ({row['id']})")
            print(f"  {row['why']}")


def cmd_inventory(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"Inventory root does not exist: {root}")
    payload = build_repo_inventory(root)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0
    _print_inventory_text(payload)
    return 0


def cmd_heimdall(args: argparse.Namespace) -> int:
    argv = [
        "--workspace",
        str(args.workspace),
        "--state-file",
        args.state_file,
        "--daily-dir",
        args.daily_dir,
    ]
    for flag_name, cli_flag in (
        ("dry_run", "--dry-run"),
        ("note", "--note"),
        ("show_json", "--show-json"),
        ("ratatoskr", "--ratatoskr"),
    ):
        if getattr(args, flag_name):
            argv.append(cli_flag)
    for attr, flag in (
        ("timezone", "--timezone"),
        ("channel", "--channel"),
        ("chatType", "--chat-type"),
        ("runtimeCore", "--runtime-core"),
        ("sessionKey", "--session-key"),
        ("openclawVersion", "--openclaw-version"),
        ("build", "--build"),
        ("model", "--model"),
        ("providerAuth", "--provider-auth"),
        ("hostLabel", "--host-label"),
        ("osKernel", "--os-kernel"),
        ("shell", "--shell"),
        ("node", "--node"),
        ("reasoning", "--reasoning"),
        ("elevation", "--elevation"),
    ):
        value = getattr(args, attr)
        if value is not None:
            argv.extend([flag, str(value)])
    return heimdall_main(argv)


def cmd_ratatoskr(args: argparse.Namespace) -> int:
    argv = [
        "--workspace",
        str(args.workspace),
        "--daily-dir",
        args.daily_dir,
        "--promotion-file",
        args.promotion_file,
    ]
    if args.event_json:
        argv.extend(["--event-json", args.event_json])
    if args.event_file:
        argv.extend(["--event-file", args.event_file])
    if args.dry_run:
        argv.append("--dry-run")
    if args.show_event:
        argv.append("--show-event")
    return ratatoskr_main(argv)


def _print_raven_status(rows: list[dict]) -> None:
    print("RAVENS flights\n")
    if not rows:
        print("(no flights)")
        return

    for row in rows:
        actors = ",".join(row.get("actors") or [])
        print(
            f"- {row.get('id')} [{row.get('status', 'unknown')}] "
            f"trigger={row.get('trigger', '?')} actors={actors or '?'} "
            f"updated={row.get('updatedAt', row.get('createdAt', '?'))}"
        )
        print(f"  purpose: {row.get('purpose', '')}")


def cmd_raven_launch(args: argparse.Namespace) -> int:
    purpose = _compact(" ".join(args.purpose))
    if not purpose:
        raise SystemExit("`ygg raven launch` requires a purpose.")

    flight = launch_flight(
        state_runtime_dir=RAVEN_STATE_DIR,
        purpose=purpose,
        trigger=_slugify(args.trigger),
        actors=parse_actors(args.actors),
        initiated_by=_slugify(args.initiated_by),
        flight_id=args.flight_id,
    )

    if args.json:
        print(json.dumps(flight, indent=2, ensure_ascii=False))
        return 0

    print("RAVENS launch")
    print(f"- id: {flight['id']}")
    print(f"- status: {flight['status']}")
    print(f"- trigger: {flight['trigger']}")
    print(f"- actors: {', '.join(flight['actors'])}")
    print(f"- purpose: {flight['purpose']}")
    print(f"- log: {flight['logFile']}")
    return 0


def cmd_raven_status(args: argparse.Namespace) -> int:
    rows = list_flights(RAVEN_STATE_DIR)
    if args.limit:
        rows = rows[: args.limit]

    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return 0

    _print_raven_status(rows)
    return 0


def cmd_raven_inspect(args: argparse.Namespace) -> int:
    try:
        payload = load_flight(RAVEN_STATE_DIR, args.flight_id)
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from exc

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def cmd_raven_trace(args: argparse.Namespace) -> int:
    try:
        rows = load_flight_log(RAVEN_STATE_DIR, args.flight_id)
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from exc

    if args.limit:
        rows = rows[-args.limit :]

    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return 0

    print(f"RAVENS trace — {args.flight_id}")
    for row in rows:
        ts = row.get("timestamp", "?")
        actor = row.get("actor", "unknown")
        phase = row.get("phase", "event")
        action = row.get("action", "?")
        target = row.get("target", "?")
        note = row.get("notes") or row.get("outcome") or ""
        print(f"- {ts} | {actor} | {phase} | {action} -> {target}")
        if note:
            print(f"  note: {note}")
    return 0


def cmd_raven_probe(args: argparse.Namespace) -> int:
    try:
        payload = record_probe(
            state_runtime_dir=RAVEN_STATE_DIR,
            flight_id=args.flight_id,
            actor=_slugify(args.actor),
            surface=args.surface,
            action=_slugify(args.action),
            outcome=args.outcome,
            tags=args.tag or [],
            notes=args.notes or "",
        )
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from exc

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    print("RAVENS probe")
    print(f"- flight: {payload['flightId']}")
    print(f"- actor: {payload['actor']}")
    print(f"- action: {payload['action']}")
    print(f"- surface: {payload['target']}")
    print(f"- outcome: {payload['outcome']}")
    return 0


def cmd_raven_aviary(args: argparse.Namespace) -> int:
    topic = _compact(" ".join(args.topic))
    if not topic:
        raise SystemExit("`ygg raven aviary` requires a topic.")

    try:
        payload = record_aviary_exchange(
            state_runtime_dir=RAVEN_STATE_DIR,
            flight_id=args.flight_id,
            actors=parse_actors(args.actors),
            topic=topic,
            claims=args.claim or [],
            outcome=args.outcome,
            notes=args.notes or "",
        )
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from exc

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    print("RAVENS aviary")
    print(f"- flight: {payload['flightId']}")
    print(f"- actors: {', '.join(payload['actors'])}")
    print(f"- topic: {payload['topic']}")
    print(f"- outcome: {payload['outcome']}")
    print(f"- file: {payload['file']}")
    return 0


def cmd_raven_return(args: argparse.Namespace) -> int:
    try:
        payload = create_return_packet(
            state_runtime_dir=RAVEN_STATE_DIR,
            flight_id=args.flight_id,
            claim_tier=args.claim_tier,
            adjudication=args.adjudication,
            promotion=args.promotion,
            evidence=args.evidence or [],
            recommendation=args.recommendation or "",
            failure_conditions=args.failure_condition or [],
            overwrite=args.force,
        )
    except (FileNotFoundError, FileExistsError) as exc:
        raise SystemExit(str(exc)) from exc

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    print("RAVENS return")
    print(f"- id: {payload['id']}")
    print(f"- return file: {payload['returnFile']}")
    print(f"- adjudication: {payload['adjudication']}")
    print(f"- promotion: {payload['promotion']}")
    return 0


def cmd_raven_adjudicate(args: argparse.Namespace) -> int:
    try:
        payload = adjudicate_flight(
            state_runtime_dir=RAVEN_STATE_DIR,
            flight_id=args.flight_id,
            disposition=args.disposition,
        )
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from exc

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    print("RAVENS adjudication")
    print(f"- id: {payload['id']}")
    print(f"- adjudication: {payload['adjudication']}")
    print(f"- status: {payload['status']}")
    return 0


def cmd_graft_propose(args: argparse.Namespace) -> int:
    title = _compact(" ".join(args.title))
    if not title:
        raise SystemExit("`ygg graft propose` requires a title.")

    try:
        payload = propose_graft(
            state_runtime_dir=RAVEN_STATE_DIR,
            title=title,
            target_attachment=args.target_attachment,
            why_now=args.why_now or "",
            risk_class=args.risk_class,
            source_flight=args.source_flight,
            proposal_id=args.id,
            overwrite=args.force,
        )
    except FileExistsError as exc:
        raise SystemExit(str(exc)) from exc

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    print("GRAFT proposal")
    print(f"- id: {payload['id']}")
    print(f"- title: {payload['title']}")
    print(f"- target: {payload['targetAttachment']}")
    print(f"- risk: {payload['riskClass']}")
    print(f"- file: {payload['file']}")
    return 0


def cmd_beak_propose(args: argparse.Namespace) -> int:
    title = _compact(" ".join(args.title))
    if not title:
        raise SystemExit("`ygg beak propose` requires a title.")

    try:
        payload = propose_beak(
            state_runtime_dir=RAVEN_STATE_DIR,
            title=title,
            beak_class=args.beak_class,
            target=args.target,
            problem_type=args.problem_type,
            evidence=args.evidence or [],
            source_flight=args.source_flight,
            proposal_id=args.id,
            overwrite=args.force,
        )
    except FileExistsError as exc:
        raise SystemExit(str(exc)) from exc

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    print("BEAK proposal")
    print(f"- id: {payload['id']}")
    print(f"- class: {payload['class']}")
    print(f"- target: {payload['target']}")
    print(f"- problem: {payload['problemType']}")
    print(f"- file: {payload['file']}")
    return 0


def cmd_branch(args: argparse.Namespace) -> int:
    domain = _slugify(args.domain)
    task = _slugify(args.task)

    objective = args.objective or f"Work on {task.replace('-', ' ')}"
    current_state = args.current_state or "Branch created via ygg; awaiting execution details."
    next_action = args.next_action or "Clarify scope and begin execution."

    cmd = [
        sys.executable,
        str(RESUME_SCRIPT),
        "checkpoint",
        domain,
        task,
        "--status",
        args.task_status,
        "--priority",
        args.priority,
        "--objective",
        objective,
        "--current-state",
        current_state,
        "--next-action",
        next_action,
    ]

    for item in args.locked or []:
        cmd.extend(["--locked", item])
    for item in args.rejected or []:
        cmd.extend(["--rejected", item])
    for item in args.reopen or []:
        cmd.extend(["--reopen", item])
    for item in args.artifact or []:
        cmd.extend(["--artifact", item])
    if args.agent:
        cmd.extend(["--agent", args.agent])

    if args.dry_run:
        print("Ygg branch dry-run")
        print(f"- domain: {domain}")
        print(f"- task: {task}")
        print(f"- objective: {objective}")
        print(f"- next action: {next_action}")
        print(f"- command: {_render_cmd(cmd)}")
        return 0

    rc = _run(cmd)
    if rc != 0:
        return rc
    return _run([sys.executable, str(RESUME_SCRIPT), "status", domain])


def cmd_resume(args: argparse.Namespace) -> int:
    domain, task = _resolve_target(args.domain, args.task, require_task=False, verb="resume")

    cmd = [sys.executable, str(RESUME_SCRIPT), "open", domain]
    if task:
        cmd.append(task)
    if args.semantic:
        cmd.append("--semantic")
    if args.max_chars:
        cmd.extend(["--max-chars", str(args.max_chars)])
    if args.agent:
        cmd.extend(["--agent", args.agent])
    if not args.print_only:
        cmd.append("--launch")
    if args.openclaw_bin != DEFAULT_OPENCLAW_BIN:
        cmd.extend(["--openclaw-bin", args.openclaw_bin])
    return _run(cmd)


def cmd_forge(args: argparse.Namespace) -> int:
    domain, task = _resolve_target(args.domain, args.task, require_task=True, verb="forge")
    request = _compact(" ".join(args.request)) or f"Implement work for {domain} / {task}."
    if args.print_worker_command:
        print(
            _build_forge_worker_command(
                domain=domain,
                task=task,
                request=request,
                cwd=args.cwd,
                openclaw_bin=args.openclaw_bin,
                wake_now=bool(args.wake_now),
            )
        )
        return 0
    packet = _forced_packet(
        request=request,
        action="suggest_spawn_codex",
        reason="Forced implementation/delegation entry via ygg forge.",
        session=args.session,
        needs_approval=False,
        domain=domain,
        task=task,
        confidence=0.96,
    )
    return _launch_packet(packet, session=args.session, openclaw_bin=args.openclaw_bin, print_packet=args.print_packet)


def cmd_promote(args: argparse.Namespace) -> int:
    if _is_continuity_promote(args):
        if args.domain or args.task:
            raise SystemExit("Continuity promote does not accept domain/task positional targets.")
        if args.disposition not in PROMOTION_DISPOSITIONS:
            allowed = ", ".join(sorted(PROMOTION_DISPOSITIONS))
            raise SystemExit(f"Continuity promote requires one of: {allowed}")
        if args.dry_run:
            record = {
                "lane": args.lane,
                "summary": args.summary,
                "disposition": args.disposition,
                "promotion_target": args.promotion_target,
                "evidence": args.evidence,
                "next_action": args.next_action,
            }
            print("Ygg continuity promote dry-run")
            print(json.dumps(record, indent=2, ensure_ascii=False))
            return 0
        try:
            path = _write_continuity_from_args(args)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        print(json.dumps({"status": "ok", "promotion_checkpoint": str(path.relative_to(YGG_HOME))}, indent=2, ensure_ascii=False))
        return 0

    if not args.domain or not args.task:
        raise SystemExit("Baton promote requires domain and task, or use --lane/--summary for continuity promote.")
    if args.disposition not in {"no-promote", "log-daily", "promote-durable", "escalate-hitl"}:
        raise SystemExit("Baton promote disposition must be one of: no-promote, log-daily, promote-durable, escalate-hitl")

    domain = _slugify(args.domain)
    task = _slugify(args.task)
    record = {
        "timestamp": _now_iso(),
        "domain": domain,
        "task": task,
        "disposition": args.disposition,
        "note": args.note or "",
        "artifacts": args.artifact or [],
        "finish": bool(args.finish),
    }

    checkpoint_cmd = [sys.executable, str(RESUME_SCRIPT), "checkpoint", domain, task]
    finish_cmd = [sys.executable, str(RESUME_SCRIPT), "finish", domain, task]
    if args.note:
        finish_cmd.extend(["--note", args.note])

    if args.dry_run:
        print("Ygg promote dry-run")
        print(json.dumps(record, indent=2, ensure_ascii=False))
        if args.disposition == "log-daily" and not args.finish:
            print(f"daily command: {_render_cmd(checkpoint_cmd)}")
        if args.finish:
            print(f"finish command: {_render_cmd(finish_cmd)}")
        return 0

    _append_promotion_record(record)

    if args.disposition == "log-daily" and not args.finish:
        rc = _run(checkpoint_cmd)
        if rc != 0:
            return rc

    if args.finish:
        rc = _run(finish_cmd)
        if rc != 0:
            return rc

    print(f"promotion recorded: {PROMOTION_LOG_JSONL}")
    print(f"notes updated: {PROMOTION_LOG_MD}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ygg",
        description="Ygg CLI — a thin control surface over planner/resume baton flows.",
    )
    sub = parser.add_subparsers(dest="verb", required=True)

    explain_p = sub.add_parser("explain", help="Self-teaching vocabulary: explain what a Ygg verb does")
    explain_p.add_argument("verb", nargs="?", help="Verb to explain (e.g. suggest, branch, promote)")
    explain_p.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text")
    explain_p.set_defaults(func=cmd_explain, invoked_as="explain")

    help_p = sub.add_parser("help", help="Alias for `ygg explain`")
    help_p.add_argument("verb", nargs="?", help="Verb to explain (e.g. suggest, branch, promote)")
    help_p.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text")
    help_p.set_defaults(func=cmd_explain, invoked_as="help")

    suggest_p = sub.add_parser("suggest", help="Translate natural-language intent into candidate Ygg commands")
    suggest_p.add_argument("request", nargs="+", help="Freeform natural-language request")
    suggest_p.add_argument("--domain", help="Optional domain hint for command generation")
    suggest_p.add_argument("--task", help="Optional task hint for command generation")
    suggest_p.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text")
    suggest_p.set_defaults(func=cmd_suggest)

    mode_p = sub.add_parser("mode", help="Persist or inspect persona-mode override state")
    mode_p.add_argument("action", choices=["nyx", "solace", "get", "clear"], help="Set Nyx/Solace override, inspect current mode, or clear override")
    mode_p.add_argument("--session", default=DEFAULT_SESSION, help=f"Session suffix to notify live mode changes (default: {DEFAULT_SESSION})")
    mode_p.add_argument("--openclaw-bin", default=DEFAULT_OPENCLAW_BIN, help="OpenClaw binary path")
    mode_p.add_argument("--print-message", action="store_true", help="Print the switch directive instead of notifying a session")
    mode_p.add_argument("--no-notify", action="store_true", help="Persist mode state without sending a live session message")
    mode_p.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text")
    mode_p.set_defaults(func=cmd_mode)

    run_p = sub.add_parser("run", help="Fast alias for persona mode control (e.g. `ygg run nyx`)")
    run_p.add_argument("action", choices=["nyx", "solace", "auto", "get", "clear"], help="Set Nyx/Solace override, inspect current mode, or reset to auto")
    run_p.add_argument("--session", default=DEFAULT_SESSION, help=f"Session suffix to notify live mode changes (default: {DEFAULT_SESSION})")
    run_p.add_argument("--openclaw-bin", default=DEFAULT_OPENCLAW_BIN, help="OpenClaw binary path")
    run_p.add_argument("--print-message", action="store_true", help="Print the switch directive instead of notifying a session")
    run_p.add_argument("--no-notify", action="store_true", help="Persist mode state without sending a live session message")
    run_p.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text")
    run_p.set_defaults(func=cmd_run)

    nyx_p = sub.add_parser("nyx", help="Direct Nyx front door; optional request text yields Nyx-shaped routing output")
    nyx_p.add_argument("request", nargs="*", help="Optional freeform request text for Nyx interpretation")
    nyx_p.add_argument("--session", default=DEFAULT_SESSION, help=f"Session suffix to notify live mode changes (default: {DEFAULT_SESSION})")
    nyx_p.add_argument("--openclaw-bin", default=DEFAULT_OPENCLAW_BIN, help="OpenClaw binary path")
    nyx_p.add_argument("--notify", action="store_true", help="Also notify the live session when request text is supplied")
    nyx_p.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text")
    nyx_p.set_defaults(func=cmd_nyx)

    work_p = sub.add_parser("work", help="Natural-language front door into the planner-aware work wrapper")
    work_p.add_argument("request", nargs="*", help="Freeform request text")
    work_p.set_defaults(func=cmd_work)

    paths_p = sub.add_parser("paths", help="Show or validate path-contract resolution")
    paths_p.add_argument("action", nargs="?", choices=["show", "check"], default="show", help="show (default) or check")
    paths_p.add_argument("--paths-file", help="Explicit path-contract file path")
    paths_p.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text")
    paths_p.set_defaults(func=cmd_paths)

    bootstrap_p = sub.add_parser("bootstrap", help="Inspect Ygg bootstrap profile and component resolution")
    bootstrap_sub = bootstrap_p.add_subparsers(dest="bootstrap_cmd", required=True)
    bootstrap_inspect_p = bootstrap_sub.add_parser("inspect", help="Show resolved bootstrap profile, components, packages, and path contract preview")
    bootstrap_inspect_p.add_argument("--profile", default=DEFAULT_BOOTSTRAP_PROFILE, help=f"Bootstrap profile name or file (default: {DEFAULT_BOOTSTRAP_PROFILE})")
    bootstrap_inspect_p.add_argument("--registry", default="state/profiles/components.yaml", help="Component registry path relative to Ygg root unless absolute")
    bootstrap_inspect_p.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text")
    bootstrap_inspect_p.set_defaults(func=cmd_bootstrap_inspect)

    inventory_p = sub.add_parser("inventory", help="Inventory the Ygg repo itself: systems, bridges, state surfaces, and next targets")
    inventory_p.add_argument("--root", default=str(YGG_HOME), help="Repo root to inventory (default: current Ygg root)")
    inventory_p.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text")
    inventory_p.set_defaults(func=cmd_inventory)

    heimdall_p = sub.add_parser("heimdall", help="Refresh Ygg-owned runtime embodiment state")
    heimdall_p.add_argument("--workspace", default=str(YGG_HOME), help="Workspace root (default: Ygg root)")
    heimdall_p.add_argument("--state-file", default="state/runtime/ygg-self.json", help="Runtime self snapshot path relative to workspace unless absolute")
    heimdall_p.add_argument("--daily-dir", default="state/notes/daily", help="Daily note directory relative to workspace unless absolute")
    heimdall_p.add_argument("--dry-run", action="store_true", help="Compute without writing state")
    heimdall_p.add_argument("--note", action="store_true", help="Append a runtime note when meaningful fields changed")
    heimdall_p.add_argument("--show-json", action="store_true", help="Print resulting JSON snapshot")
    heimdall_p.add_argument("--ratatoskr", action="store_true", help="Route meaningful changes through Ratatoskr instead of direct note writing")
    heimdall_p.add_argument("--timezone")
    heimdall_p.add_argument("--channel")
    heimdall_p.add_argument("--chat-type", dest="chatType")
    heimdall_p.add_argument("--runtime-core", dest="runtimeCore")
    heimdall_p.add_argument("--session-key", dest="sessionKey")
    heimdall_p.add_argument("--openclaw-version", dest="openclawVersion")
    heimdall_p.add_argument("--build")
    heimdall_p.add_argument("--model")
    heimdall_p.add_argument("--provider-auth", dest="providerAuth")
    heimdall_p.add_argument("--host-label", dest="hostLabel")
    heimdall_p.add_argument("--os-kernel", dest="osKernel")
    heimdall_p.add_argument("--shell")
    heimdall_p.add_argument("--node")
    heimdall_p.add_argument("--reasoning")
    heimdall_p.add_argument("--elevation")
    heimdall_p.set_defaults(func=cmd_heimdall)

    ratatoskr_p = sub.add_parser("ratatoskr", help="Route structured continuity events into Ygg-owned sinks")
    ratatoskr_p.add_argument("--workspace", default=str(YGG_HOME), help="Workspace root (default: Ygg root)")
    ratatoskr_p.add_argument("--event-json", help="Inline JSON event payload")
    ratatoskr_p.add_argument("--event-file", help="Path to JSON event payload")
    ratatoskr_p.add_argument("--daily-dir", default="state/notes/daily", help="Daily note directory relative to workspace unless absolute")
    ratatoskr_p.add_argument("--promotion-file", default="state/notes/promotion-candidates.md", help="Promotion note path relative to workspace unless absolute")
    ratatoskr_p.add_argument("--dry-run", action="store_true", help="Show routing result without writing")
    ratatoskr_p.add_argument("--show-event", action="store_true", help="Print the event payload instead of the routing result")
    ratatoskr_p.set_defaults(func=cmd_ratatoskr)

    raven_p = sub.add_parser("raven", help="RAVENS v1 flight operations")
    raven_sub = raven_p.add_subparsers(dest="raven_cmd", required=True)

    raven_launch_p = raven_sub.add_parser("launch", help="Launch a raven flight")
    raven_launch_p.add_argument("purpose", nargs="+", help="Flight purpose/objective")
    raven_launch_p.add_argument("--trigger", default="human-request", help="Trigger type (default: human-request)")
    raven_launch_p.add_argument("--actors", default="huginn,muninn", help="Comma/space-separated actors (default: huginn,muninn)")
    raven_launch_p.add_argument("--initiated-by", default="spine", help="Initiator id (default: spine)")
    raven_launch_p.add_argument("--flight-id", help="Optional explicit flight id")
    raven_launch_p.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    raven_launch_p.set_defaults(func=cmd_raven_launch)

    raven_status_p = raven_sub.add_parser("status", help="List known raven flights")
    raven_status_p.add_argument("--limit", type=int, default=20, help="Max flights to show (default: 20)")
    raven_status_p.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    raven_status_p.set_defaults(func=cmd_raven_status)

    raven_inspect_p = raven_sub.add_parser("inspect", help="Inspect one raven flight by id")
    raven_inspect_p.add_argument("flight_id", help="Flight id (e.g., RAVEN-...)")
    raven_inspect_p.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    raven_inspect_p.set_defaults(func=cmd_raven_inspect)

    raven_trace_p = raven_sub.add_parser("trace", help="Show flight event log")
    raven_trace_p.add_argument("flight_id", help="Flight id (e.g., RAVEN-...)")
    raven_trace_p.add_argument("--limit", type=int, default=50, help="Max log events to show (default: 50)")
    raven_trace_p.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    raven_trace_p.set_defaults(func=cmd_raven_trace)

    raven_probe_p = raven_sub.add_parser("probe", help="Record an observed surface interaction for a flight")
    raven_probe_p.add_argument("flight_id", help="Flight id (e.g., RAVEN-...)")
    raven_probe_p.add_argument("surface", help="Touched surface or resource")
    raven_probe_p.add_argument("--action", default="observe", help="Probe action label (default: observe)")
    raven_probe_p.add_argument("--actor", default="huginn", help="Actor recording the probe (default: huginn)")
    raven_probe_p.add_argument("--outcome", default="observed", help="Outcome summary (default: observed)")
    raven_probe_p.add_argument("--tag", action="append", help="Optional repeatable tags")
    raven_probe_p.add_argument("--notes", help="Optional freeform notes")
    raven_probe_p.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    raven_probe_p.set_defaults(func=cmd_raven_probe)

    raven_aviary_p = raven_sub.add_parser("aviary", help="Record a bounded raven-to-raven exchange")
    raven_aviary_p.add_argument("flight_id", help="Flight id (e.g., RAVEN-...)")
    raven_aviary_p.add_argument("topic", nargs="+", help="Topic of the exchange")
    raven_aviary_p.add_argument("--actors", default="huginn,muninn", help="Comma/space-separated actors (default: huginn,muninn)")
    raven_aviary_p.add_argument("--claim", action="append", help="Repeatable claim exchanged in aviary")
    raven_aviary_p.add_argument("--outcome", default="park-for-spine", help="Outcome summary (default: park-for-spine)")
    raven_aviary_p.add_argument("--notes", help="Optional freeform notes")
    raven_aviary_p.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    raven_aviary_p.set_defaults(func=cmd_raven_aviary)

    raven_return_p = raven_sub.add_parser("return", help="Create a structured return packet for a flight")
    raven_return_p.add_argument("flight_id", help="Flight id (e.g., RAVEN-...)")
    raven_return_p.add_argument("--claim-tier", default="defensible-now", help="Claim tier label (default: defensible-now)")
    raven_return_p.add_argument(
        "--adjudication",
        default="PARK",
        choices=["REJECT", "PARK", "TRIAL", "ADOPT", "ESCALATE_HITL"],
        help="Spine adjudication class",
    )
    raven_return_p.add_argument(
        "--promotion",
        default="LOG_DAILY",
        choices=["NO_PROMOTE", "LOG_DAILY", "PROMOTE_DURABLE", "ESCALATE_HITL"],
        help="Promotion/disposition class",
    )
    raven_return_p.add_argument("--evidence", action="append", help="Evidence reference (repeatable)")
    raven_return_p.add_argument("--failure-condition", action="append", help="Failure condition bullet (repeatable)")
    raven_return_p.add_argument("--recommendation", help="Recommendation summary text")
    raven_return_p.add_argument("--force", action="store_true", help="Overwrite return file if it already exists")
    raven_return_p.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    raven_return_p.set_defaults(func=cmd_raven_return)

    raven_adjudicate_p = raven_sub.add_parser("adjudicate", help="Record a spine adjudication for a flight")
    raven_adjudicate_p.add_argument("flight_id", help="Flight id (e.g., RAVEN-...)")
    raven_adjudicate_p.add_argument(
        "disposition",
        choices=["REJECT", "PARK", "TRIAL", "ADOPT", "ESCALATE_HITL"],
        help="Spine adjudication/disposition class",
    )
    raven_adjudicate_p.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    raven_adjudicate_p.set_defaults(func=cmd_raven_adjudicate)

    graft_p = sub.add_parser("graft", help="Propose additive structural growth artifacts")
    graft_sub = graft_p.add_subparsers(dest="graft_cmd", required=True)

    graft_propose_p = graft_sub.add_parser("propose", help="Create a graft proposal artifact")
    graft_propose_p.add_argument("title", nargs="+", help="Proposal title")
    graft_propose_p.add_argument("--target-attachment", default="state/policy/", help="Attachment point path/area")
    graft_propose_p.add_argument("--why-now", help="Why this graft is needed now")
    graft_propose_p.add_argument("--risk-class", default="medium", help="Risk class (default: medium)")
    graft_propose_p.add_argument("--source-flight", help="Optional source raven flight id")
    graft_propose_p.add_argument("--id", help="Optional explicit proposal id")
    graft_propose_p.add_argument("--force", action="store_true", help="Overwrite artifact if id already exists")
    graft_propose_p.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    graft_propose_p.set_defaults(func=cmd_graft_propose)

    beak_p = sub.add_parser("beak", help="Propose subtractive/reshaping actions (proposal-only)")
    beak_sub = beak_p.add_subparsers(dest="beak_cmd", required=True)

    beak_propose_p = beak_sub.add_parser("propose", help="Create a beak proposal artifact")
    beak_propose_p.add_argument("title", nargs="+", help="Proposal title")
    beak_propose_p.add_argument("--class", dest="beak_class", choices=["soft", "hard"], default="soft", help="Beak class (default: soft)")
    beak_propose_p.add_argument("--target", default="<target>", help="Target structure/path")
    beak_propose_p.add_argument(
        "--problem-type",
        choices=["rot", "duplication", "drift", "deadwood", "misgrowth"],
        default="drift",
        help="Problem class (default: drift)",
    )
    beak_propose_p.add_argument("--evidence", action="append", help="Evidence reference (repeatable)")
    beak_propose_p.add_argument("--source-flight", help="Optional source raven flight id")
    beak_propose_p.add_argument("--id", help="Optional explicit proposal id")
    beak_propose_p.add_argument("--force", action="store_true", help="Overwrite artifact if id already exists")
    beak_propose_p.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    beak_propose_p.set_defaults(func=cmd_beak_propose)

    root_p = sub.add_parser("root", help="Force direct planner-spine entry with no route guess")
    root_p.add_argument("request", nargs="*", help="Optional context text for the planner")
    root_p.add_argument("--session", default=DEFAULT_SESSION, help=f"Planner session suffix (default: {DEFAULT_SESSION})")
    root_p.add_argument("--openclaw-bin", default=DEFAULT_OPENCLAW_BIN, help="OpenClaw binary path")
    root_p.add_argument("--print-packet", action="store_true", help="Print the planner packet instead of launching")
    root_p.set_defaults(func=cmd_root)

    branch_p = sub.add_parser("branch", help="Create or refresh a bounded task lane in baton state")
    branch_p.add_argument("domain", help="Domain id/name")
    branch_p.add_argument("task", help="Task id/name")
    branch_p.add_argument("--objective", help="Objective text for the branch")
    branch_p.add_argument("--current-state", help="Current state text")
    branch_p.add_argument("--next-action", help="Next action text")
    branch_p.add_argument("--status", dest="task_status", default="active", help="Task status (default: active)")
    branch_p.add_argument("--priority", default="medium", help="Task priority (default: medium)")
    branch_p.add_argument("--locked", action="append", help="Locked decision bullet (repeatable)")
    branch_p.add_argument("--rejected", action="append", help="Rejected-path bullet (repeatable)")
    branch_p.add_argument("--reopen", action="append", help="Reopen-only-if bullet (repeatable)")
    branch_p.add_argument("--artifact", action="append", help="Relevant artifact bullet (repeatable)")
    branch_p.add_argument("--agent", help="Agent override for baton/session lookup")
    branch_p.add_argument("--dry-run", action="store_true", help="Print the underlying checkpoint command without running it")
    branch_p.set_defaults(func=cmd_branch)

    resume_p = sub.add_parser("resume", help="Resume a lane with baton-aware continuity context")
    resume_p.add_argument("domain", nargs="?", help="Domain id/name")
    resume_p.add_argument("task", nargs="?", help="Task id/name")
    resume_p.add_argument("--semantic", action="store_true", help="Add semantic recall refs when building the resume packet")
    resume_p.add_argument("--max-chars", type=int, default=1800, help="Resume packet max chars (default: 1800)")
    resume_p.add_argument("--agent", help="Agent override for baton/session lookup")
    resume_p.add_argument("--openclaw-bin", default=DEFAULT_OPENCLAW_BIN, help="OpenClaw binary path")
    resume_p.add_argument("--print-only", action="store_true", help="Print the resume packet instead of launching")
    resume_p.set_defaults(func=cmd_resume)

    forge_p = sub.add_parser("forge", help="Open planner with an implementation/delegation route bias")
    forge_p.add_argument("request", nargs="*", help="Optional implementation context text")
    forge_p.add_argument("--domain", help="Target domain (defaults to sole active task when possible)")
    forge_p.add_argument("--task", help="Target task")
    forge_p.add_argument("--session", default=DEFAULT_SESSION, help=f"Planner session suffix (default: {DEFAULT_SESSION})")
    forge_p.add_argument("--openclaw-bin", default=DEFAULT_OPENCLAW_BIN, help="OpenClaw binary path")
    forge_p.add_argument("--print-packet", action="store_true", help="Print the planner packet instead of launching")
    forge_p.add_argument("--print-worker-command", action="store_true", help="Print a ready-to-run Codex worker command instead of launching planner")
    forge_p.add_argument("--wake-now", action="store_true", help="Include an immediate OpenClaw wake hook in the printed worker command")
    forge_p.add_argument("--cwd", help="Working directory to embed in the printed worker command (defaults to current directory)")
    forge_p.set_defaults(func=cmd_forge)

    checkpoint_p = sub.add_parser("checkpoint", help="Write an SC continuity checkpoint into Ygg state")
    checkpoint_p.add_argument("--lane", required=True, help="Continuity lane name")
    checkpoint_p.add_argument("--summary", required=True, help="Short outcome summary")
    checkpoint_p.add_argument(
        "--disposition",
        required=True,
        choices=sorted(CONTINUITY_DISPOSITIONS),
        help="Continuity disposition",
    )
    checkpoint_p.add_argument("--promotion-target", default="", help="Promotion target hint when disposition promotes")
    checkpoint_p.add_argument("--evidence", default="", help="Short evidence reference")
    checkpoint_p.add_argument("--next-action", default="", help="Suggested next action")
    checkpoint_p.set_defaults(func=cmd_checkpoint)

    promote_p = sub.add_parser("promote", help="Record an explicit branch disposition / promotion event")
    promote_p.add_argument("domain", nargs="?", help="Domain id/name")
    promote_p.add_argument("task", nargs="?", help="Task id/name")
    promote_p.add_argument(
        "--disposition",
        required=True,
        help="Disposition to record",
    )
    promote_p.add_argument("--note", help="Optional note explaining the disposition")
    promote_p.add_argument("--artifact", action="append", help="Artifact path/reference to include (repeatable)")
    promote_p.add_argument("--finish", action="store_true", help="Also mark the task finished in baton state")
    promote_p.add_argument("--dry-run", action="store_true", help="Print the promotion record/actions without writing them")
    promote_p.add_argument("--lane", help="Continuity lane name for SC-compatible promote flow")
    promote_p.add_argument("--summary", help="Continuity summary for SC-compatible promote flow")
    promote_p.add_argument("--promotion-target", default="", help="Promotion target for SC-compatible promote flow")
    promote_p.add_argument("--evidence", default="", help="Evidence note for SC-compatible promote flow")
    promote_p.add_argument("--next-action", default="", help="Next action for SC-compatible promote flow")
    promote_p.set_defaults(func=cmd_promote)

    status_p = sub.add_parser("status", help="Inspect tracked baton state")
    status_p.add_argument("domain", nargs="?", help="Optional domain filter")
    status_p.add_argument("--continuity", action="store_true", help="Show the latest SC continuity checkpoint instead of baton state")
    status_p.set_defaults(func=cmd_status)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
