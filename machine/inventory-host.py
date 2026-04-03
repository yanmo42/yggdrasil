#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SELF = Path(__file__).resolve()
LIB_ROOT = SELF.parents[1] / "lib"
if str(LIB_ROOT) not in sys.path:
    sys.path.insert(0, str(LIB_ROOT))

from ygg.inventory import build_inventory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inventory the current host for Ygg kernelization and portability planning."
    )
    parser.add_argument(
        "--root",
        default=str(Path.home()),
        help="Filesystem root to inventory (default: $HOME).",
    )
    parser.add_argument(
        "--path-contract",
        default=None,
        help="Optional explicit path to ygg-paths.yaml.",
    )
    parser.add_argument(
        "--max-repo-depth",
        type=int,
        default=3,
        help="Maximum directory depth for git repo discovery (default: 3).",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the JSON output.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_inventory(
        args.root,
        max_repo_depth=args.max_repo_depth,
        path_override=args.path_contract,
    )
    indent = 2 if args.pretty else None
    json.dump(payload, sys.stdout, indent=indent)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
