"""Switch controls on and off, and start the labs over.

    python lab.py                     which controls are on
    python lab.py on approvals        switch one on (edits controls.toml)
    python lab.py off approvals       switch one off
    python lab.py on all              every control on
    python lab.py reset               every control off, release history cleared, v1 live again

This does exactly what editing controls.toml by hand does. It exists for live
demos, where one command beats switching to an editor.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import fields

from bankagent.settings import CONTROLS_FILE, STATE_DIR, Controls

NAMES = [f.name for f in fields(Controls)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Switch controls on and off, and start the labs over.")
    commands = parser.add_subparsers(dest="command")
    for verb in ("on", "off"):
        commands.add_parser(verb, help=f"switch controls {verb}").add_argument(
            "names", nargs="+", metavar="control", help=f"one or more of: {', '.join(NAMES)}, or all"
        )
    commands.add_parser("reset", help="every control off, release history cleared")
    args = parser.parse_args(argv)

    if args.command in ("on", "off"):
        names = NAMES if args.names == ["all"] else args.names
        unknown = [n for n in names if n not in NAMES]
        if unknown:
            print(f"Unknown control(s): {', '.join(unknown)}. Pick from: {', '.join(NAMES)}, or all.", file=sys.stderr)
            return 1
        set_controls({n: args.command == "on" for n in names})
    elif args.command == "reset":
        set_controls({n: False for n in NAMES})
        for name in ("live_config.json", "release_history.json"):
            (STATE_DIR / name).unlink(missing_ok=True)
        print("Reset. Release history cleared; v1 goes live the next time anything runs.")

    print(f"Controls: {Controls.load().describe()}")
    return 0


def set_controls(values: dict[str, bool]) -> None:
    """Rewrite name = true/false lines in controls.toml, keeping its comments."""
    text = CONTROLS_FILE.read_text()
    for name, on in values.items():
        pattern = re.compile(rf"^(\s*{name}\s*=\s*)(true|false)\b", re.MULTILINE)
        text, count = pattern.subn(rf"\g<1>{'true' if on else 'false'}", text)
        if count == 0:
            text = text.rstrip("\n") + f"\n{name} = {'true' if on else 'false'}\n"
    CONTROLS_FILE.write_text(text)


if __name__ == "__main__":
    raise SystemExit(main())
