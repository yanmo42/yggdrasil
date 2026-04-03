#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SELF = Path(__file__).resolve()
LIB_ROOT = SELF.parents[1] / "lib"
if str(LIB_ROOT) not in sys.path:
    sys.path.insert(0, str(LIB_ROOT))

from ygg.bootstrap_registry import render_path_contract


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render Ygg path contract from the component registry.")
    parser.add_argument("--registry", required=True, help="Path to the component registry YAML file.")
    parser.add_argument("--profile", required=True, help="Bootstrap profile name to resolve.")
    parser.add_argument("--contract-path", required=True, help="Destination path for the rendered ygg-paths.yaml.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sys.stdout.write(
        render_path_contract(
            args.registry,
            profile=args.profile,
            contract_path=args.contract_path,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
