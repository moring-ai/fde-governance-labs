"""Replay one recorded run, step by step.

    python replay.py                                 the most recent run in traces/
    python replay.py examples/refund-incident.jsonl  a specific trace file
    python replay.py --step                          press Enter to see each next step
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from bankagent.controls.traces import latest_run, read_run, render_run
from bankagent.settings import TRACES_DIR


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay one recorded run, step by step.")
    parser.add_argument("trace", nargs="?", type=Path, help="a .jsonl trace file (default: the newest in traces/)")
    parser.add_argument("--step", action="store_true", help="pause after each step")
    args = parser.parse_args(argv)

    path = args.trace or latest_run(TRACES_DIR)
    if path is None:
        print("No traces yet. Set traces = true in controls.toml, then run chat.py.", file=sys.stderr)
        return 1

    header, steps = render_run(read_run(path))
    print(f"{header}\n{shown(path)}\n")
    for i, step in enumerate(steps, start=1):
        print(step)
        if args.step and i < len(steps):
            input("    (Enter for the next step) ")
        print()
    return 0


def shown(path: Path) -> Path:
    """The path as you'd type it from here, when it's under the current folder."""
    try:
        return path.resolve().relative_to(Path.cwd())
    except ValueError:
        return path


if __name__ == "__main__":
    raise SystemExit(main())
