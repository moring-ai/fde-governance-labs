"""Lab 3: write down every step, so you can show a reviewer exactly what happened.

One JSONL file per conversation, in traces/. Each line is one event:

    user_message  what the customer typed
    tool_call     tool, input, output, whether it is irreversible, and the
                  approval (who said yes or no; null if nobody was asked)
    agent_reply   what the agent said back

Every line also carries the run id, a timestamp, the customer the conversation
is bound to, and the version and hash of the release (prompt plus tool config)
that was live when it happened.
"""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path

from ..config import Release


def new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-") + secrets.token_hex(2)


class TraceFile:
    def __init__(self, path: Path, run_id: str, customer_id: str) -> None:
        self.path = path
        self.run_id = run_id
        self.customer_id = customer_id
        self._seq = 0

    def write(self, event: str, release: Release, **fields) -> None:
        self._seq += 1
        record = {
            "run_id": self.run_id,
            "seq": self._seq,
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "event": event,
            "customer_id": self.customer_id,
            "release": release.version,
            "release_hash": release.hash,
            **fields,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as f:
            f.write(json.dumps(record) + "\n")


class NoTrace:
    """What the starter has: nothing written down."""

    path = None

    def write(self, event: str, release: Release, **fields) -> None:
        pass


# Reading traces back -------------------------------------------------------


def read_run(path: Path) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def latest_run(traces_dir: Path) -> Path | None:
    runs = list(traces_dir.glob("*.jsonl"))
    return max(runs, key=lambda p: p.stat().st_mtime) if runs else None


def render_run(events: list[dict]) -> tuple[str, list[str]]:
    """Return a header line and one text block per step, for replay.py to print."""
    if not events:
        return "Empty trace.", []
    first = events[0]
    header = f"Run {first['run_id']} · customer {first['customer_id']} · {len(events)} steps"
    return header, [_render_step(e) for e in events]


def _render_step(e: dict) -> str:
    head = f"[{e['seq']}] {e['ts'][11:19]}  release {e['release']} ({e['release_hash']})"
    if e["event"] == "user_message":
        return f"{head}\n    customer:  {e['text']}"
    if e["event"] == "agent_reply":
        return f"{head}\n    agent:     {e['text']}"
    if e["event"] == "tool_call":
        out = e["output"]
        result = (
            f"ok {json.dumps(out['data'])}"
            if out["ok"]
            else f"refused ({out['error']}): {out['message']}"
        )
        return (
            f"{head}\n"
            f"    tool:      {e['tool']} {json.dumps(e['input'])}\n"
            f"    approval:  {_approval(e)}\n"
            f"    output:    {result}"
        )
    return f"{head}\n    {e['event']}: {json.dumps(e)}"


def _approval(e: dict) -> str:
    if not e["irreversible"]:
        return "not needed (reversible)"
    a = e["approval"]
    if a is None and e["output"]["ok"]:
        return "IRREVERSIBLE, and it ran without anyone being asked"
    if a is None:
        return "irreversible, stopped before anyone was asked"
    verdict = "approved" if a["approved"] else "refused"
    note = f" ({a['note']})" if a.get("note") else ""
    return f"irreversible, {verdict} by {a['approver']}{note}"
