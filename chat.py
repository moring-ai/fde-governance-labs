"""Talk to the support agent in your terminal.

    python chat.py                         signed in as C-1001
    python chat.py --customer C-1003       signed in as someone else
    python chat.py "What's my balance?"    send messages and exit

You are also the approver. When approvals are on, you get asked y/N here.
The bank's data resets every time chat.py starts.
"""

from __future__ import annotations

import argparse
import importlib
import json

from bankagent.app import build_agent
from bankagent.controls.approvals import ConsoleApprover
from bankagent.db import SEED
from bankagent.settings import ROOT, Controls

TRY = "What's my balance?  ·  Please refund the $40 late fee.  ·  Please close my account."


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Talk to the Example Bank support agent.")
    parser.add_argument("messages", nargs="*", help="send these messages in order, then exit")
    parser.add_argument("--customer", default="C-1001", choices=[c.customer_id for c in SEED],
                        help="the signed-in customer this conversation is bound to")
    parser.add_argument("--controls", choices=["file", "on", "off"], default="file",
                        help="file: read controls.toml (default); on/off: force every control")
    parser.add_argument("--model", metavar="MODULE:CLASS",
                        help="your own model class instead of the scripted stand-in")
    args = parser.parse_args(argv)

    controls = Controls.load(args.controls)
    agent = build_agent(controls, ConsoleApprover(), model=load_model(args.model), watch=show_tool_call)
    convo = agent.start(args.customer)
    release = agent.releases.live()
    print(f"Example Bank support · signed in as {args.customer} · release {release.version} ({release.hash})")
    print(f"Controls: {controls.describe()}")

    if args.messages:
        for text in args.messages:
            print(f"\nyou>    {text}")
            print(f"agent>  {agent.send(convo, text)}")
    else:
        print(f"Type a message, or quit. Try: {TRY}")
        while True:
            try:
                text = input("\nyou>    ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if text.lower() in ("quit", "exit"):
                break
            if text:
                print(f"agent>  {agent.send(convo, text)}")

    if convo.trace.path and convo.trace.path.exists():
        print(f"\nTrace: {convo.trace.path.relative_to(ROOT)}  (replay it: python replay.py)")
    return 0


def show_tool_call(call, result, decision) -> None:
    outcome = "ok" if result["ok"] else f"refused, {result['error']}"
    print(f"        [tool] {call.name} {json.dumps(call.args)} -> {outcome}")


def load_model(spec: str | None):
    if not spec:
        return None
    module_name, _, class_name = spec.partition(":")
    return getattr(importlib.import_module(module_name), class_name)()


if __name__ == "__main__":
    raise SystemExit(main())
