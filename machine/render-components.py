#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SELF = Path(__file__).resolve()
LIB_ROOT = SELF.parents[1] / "lib"
if str(LIB_ROOT) not in sys.path:
    sys.path.insert(0, str(LIB_ROOT))

from ygg.bootstrap_registry import render_shell_assignments


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render Ygg bootstrap component registry into shell assignments.")
    parser.add_argument("--registry", required=True, help="Path to the component registry YAML file.")
    parser.add_argument("--profile", required=True, help="Bootstrap profile name to resolve.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sys.stdout.write(render_shell_assignments(args.registry, profile=args.profile))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
