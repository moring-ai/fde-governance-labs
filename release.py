"""Ship a release, roll it back, or switch off one tool.

    python release.py status
    python release.py deploy v2
    python release.py rollback
    python release.py disable issue_refund     kill switch: this tool stops working, nothing is redeployed
    python release.py enable issue_refund
    python release.py reset                    forget every deploy; v1 goes live again

Works while chat.py is running in another terminal: the agent re-reads the live
release every turn and the kill switch on every tool call.
"""

from __future__ import annotations

import argparse
import sys

from bankagent.app import open_releases
from bankagent.config import KillSwitchUnavailable, RollbackUnavailable
from bankagent.controls.rollback import ReleaseHistory
from bankagent.settings import STATE_DIR, Controls


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deploy, roll back, and switch tools on or off.")
    parser.add_argument("--controls", choices=["file", "on", "off"], default="file",
                        help="file: read controls.toml (default); on/off: force every control")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="what is live, and what happened before")
    commands.add_parser("deploy", help="make a release live").add_argument("version")
    commands.add_parser("rollback", help="go back to the previous release")
    commands.add_parser("disable", help="kill switch: turn one tool off").add_argument("tool")
    commands.add_parser("enable", help="turn a tool back on").add_argument("tool")
    commands.add_parser("reset", help="forget every deploy and start the lab over")
    args = parser.parse_args(argv)

    if args.command == "reset":
        for name in ("live_config.json", "release_history.json"):
            (STATE_DIR / name).unlink(missing_ok=True)
        print("Cleared. v1 goes live the next time anything runs.")
        return 0

    releases = open_releases(Controls.load(args.controls))
    before = releases.live()
    try:
        if args.command == "status":
            print_status(releases)
        elif args.command == "deploy":
            live = releases.deploy(args.version)
            print(f"Deployed. Live release: {live.version} (hash {live.hash})")
        elif args.command == "rollback":
            live = releases.rollback()
            print(f"Rolled back {before.version} -> {live.version}. Live release: {live.version} (hash {live.hash})")
        elif args.command == "disable":
            releases.disable(args.tool)
            print(f"{args.tool} is switched off. Nothing was redeployed; live release is still {before.version}.")
        elif args.command == "enable":
            releases.enable(args.tool)
            print(f"{args.tool} is switched back on.")
    except (RollbackUnavailable, KillSwitchUnavailable, ValueError) as e:
        print(f"Can't {args.command}: {e}", file=sys.stderr)
        return 1
    return 0


def print_status(releases) -> None:
    live = releases.live()
    print(f"Live release:  {live.version} (hash {live.hash})")
    if not isinstance(releases, ReleaseHistory):
        print("History:       none kept. The starter overwrites the live config in place.")
        print("Kill switch:   not available in the starter.")
        return
    print(f"History:       {' -> '.join(releases.history())}")
    disabled = sorted(releases.disabled_tools())
    print(f"Kill switch:   {', '.join(disabled) + ' switched off' if disabled else 'every tool on'}")
    print("Log:")
    for entry in releases.log():
        print(f"  {entry['at']}  {entry['by']:<10} {entry['action']:<9} {entry['detail']}")


if __name__ == "__main__":
    raise SystemExit(main())
