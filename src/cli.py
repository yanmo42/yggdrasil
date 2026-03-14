#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
YGG_HOME = HOME / "ygg"
WORKSPACE = HOME / ".openclaw" / "workspace-claw-main"
WORK_SCRIPT = WORKSPACE / "scripts" / "work.py"
RESUME_SCRIPT = WORKSPACE / "scripts" / "resume.py"
STATE_DIR = YGG_HOME / "state"
NOTES_DIR = YGG_HOME / "notes"
PROMOTION_LOG_JSONL = STATE_DIR / "promotions.jsonl"
PROMOTION_LOG_MD = NOTES_DIR / "promotions.md"
DEFAULT_SESSION = "planner--main"
DEFAULT_OPENCLAW_BIN = "openclaw"

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
        "purpose": "Open the planner-aware front door for flexible natural-language routing.",
        "when_to_use": [
            "When route/target is still unclear.",
            "When you want planner oversight by default.",
        ],
        "examples": ['ygg work "add more functionality to theme selector in personal website"'],
        "next": ["suggest", "root", "status"],
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
        "purpose": "Bias planner routing toward implementation/delegation for a specific lane.",
        "when_to_use": [
            "When the next move is coding/build/fix execution.",
            "When you want implementation posture while preserving planner oversight.",
        ],
        "examples": [
            'ygg forge --domain website-dev --task theme-selector-enhancements "implement the improved theme selector UX"',
            "ygg forge --domain website-dev --task theme-selector-enhancements --print-packet",
        ],
        "next": ["promote", "status", "resume"],
    },
    "promote": {
        "purpose": "Record explicit branch disposition so meaningful outcomes do not vanish silently.",
        "when_to_use": [
            "When a branch produced a meaningful result.",
            "When you want a durable log of what happened next.",
        ],
        "examples": [
            'ygg promote website-dev theme-selector-enhancements --disposition log-daily --note "Scope clarified"',
            "ygg promote website-dev theme-selector-enhancements --disposition log-daily --dry-run",
        ],
        "next": ["status", "resume"],
    },
    "status": {
        "purpose": "Inspect tracked domains, active tasks, and next actions.",
        "when_to_use": [
            "When choosing which lane to target.",
            "When checking current baton state quickly.",
        ],
        "examples": ["ygg status", "ygg status website-dev"],
        "next": ["suggest", "resume", "branch"],
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
        raise SystemExit(
            "Ygg could not import the current workspace implementation. "
            f"Expected modules under {WORKSPACE}. Original error: {IMPORT_ERROR}"
        )


def _run(cmd: list[str]) -> int:
    proc = subprocess.run(cmd)
    return int(proc.returncode)


def _render_cmd(cmd: list[str]) -> str:
    return shlex.join(cmd)


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
        if not primary.get("executable", True):
            print("   note: template command — fill in the placeholder values first.")

    if alternatives:
        print("\nother good options:")
        for idx, item in enumerate(alternatives, start=2 if primary else 1):
            print(f"{idx}. {item['command']}")
            print(f"   why: {item['why']}")
            if not item.get("executable", True):
                print("   note: template command — fill in the placeholder values first.")

    if active_tasks:
        print("\nactive tasks:")
        for row in active_tasks:
            print(
                f"- {row['domain']} / {row['task']} [{row['status']}, {row['freshness']}] "
                f"— next: {row['next_action']}"
            )


def _print_explain_card(verb: str, card: dict[str, object]) -> None:
    print(f"ygg explain {verb}\n")
    print(f"purpose: {card['purpose']}")

    when_to_use = card.get("when_to_use") or []
    if when_to_use:
        print("\nwhen to use:")
        for item in when_to_use:
            print(f"- {item}")

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
    if not args.verb:
        verbs = sorted(EXPLAIN_CARDS.keys())
        payload = {
            "verbs": verbs,
            "hint": "Run `ygg explain <verb>` for details.",
        }
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            return 0

        print("Ygg explain\n")
        print("known verbs:")
        for v in verbs:
            print(f"- {v}: {EXPLAIN_CARDS[v]['purpose']}")
        print("\nRun `ygg explain <verb>` for full details.")
        return 0

    verb = _slugify(args.verb)
    card = EXPLAIN_CARDS.get(verb)
    if not card:
        known = ", ".join(sorted(EXPLAIN_CARDS.keys()))
        raise SystemExit(f"Unknown verb `{verb}`. Known verbs: {known}")

    payload = {
        "verb": verb,
        **card,
    }
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    _print_explain_card(verb, card)
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


def cmd_work(args: argparse.Namespace) -> int:
    return _run([sys.executable, str(WORK_SCRIPT), *args.request])


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


def cmd_status(args: argparse.Namespace) -> int:
    cmd = [sys.executable, str(RESUME_SCRIPT), "status"]
    if args.domain:
        cmd.append(_slugify(args.domain))
    return _run(cmd)


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
    explain_p.set_defaults(func=cmd_explain)

    suggest_p = sub.add_parser("suggest", help="Translate natural-language intent into candidate Ygg commands")
    suggest_p.add_argument("request", nargs="+", help="Freeform natural-language request")
    suggest_p.add_argument("--domain", help="Optional domain hint for command generation")
    suggest_p.add_argument("--task", help="Optional task hint for command generation")
    suggest_p.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text")
    suggest_p.set_defaults(func=cmd_suggest)

    work_p = sub.add_parser("work", help="Natural-language front door into the planner-aware work wrapper")
    work_p.add_argument("request", nargs="*", help="Freeform request text")
    work_p.set_defaults(func=cmd_work)

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
    forge_p.set_defaults(func=cmd_forge)

    promote_p = sub.add_parser("promote", help="Record an explicit branch disposition / promotion event")
    promote_p.add_argument("domain", help="Domain id/name")
    promote_p.add_argument("task", help="Task id/name")
    promote_p.add_argument(
        "--disposition",
        required=True,
        choices=["no-promote", "log-daily", "promote-durable", "escalate-hitl"],
        help="Disposition to record",
    )
    promote_p.add_argument("--note", help="Optional note explaining the disposition")
    promote_p.add_argument("--artifact", action="append", help="Artifact path/reference to include (repeatable)")
    promote_p.add_argument("--finish", action="store_true", help="Also mark the task finished in baton state")
    promote_p.add_argument("--dry-run", action="store_true", help="Print the promotion record/actions without writing them")
    promote_p.set_defaults(func=cmd_promote)

    status_p = sub.add_parser("status", help="Inspect tracked baton state")
    status_p.add_argument("domain", nargs="?", help="Optional domain filter")
    status_p.set_defaults(func=cmd_status)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
