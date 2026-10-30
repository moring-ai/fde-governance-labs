"""Lab 1: irreversible tools wait for a human yes/no.

The agent builds an ApprovalRequest and hands it to an Approver. Anything that
can answer decide() works: a terminal prompt (here), a ticket queue, a chat
message with two buttons. In production the answer usually comes back later,
not in the same call, but the contract is the same: a request goes out, and a
yes or no comes back with a name attached.

The request carries what the customer actually said. An approver who only sees
"Refund $95.00 to C-1003" will say yes. One who also sees that the customer
asked for their balance will spot a refund nobody asked for (Lab 5).
"""

from __future__ import annotations

import getpass
from dataclasses import dataclass
from typing import Protocol

from ..tools import describe


@dataclass(frozen=True)
class ApprovalRequest:
    tool: str
    args: dict
    customer_id: str  # the customer this conversation is bound to
    release: str      # the release that proposed the action
    customer_said: str = ""  # the customer's latest message, so the approver can compare

    def summary(self) -> str:
        return describe(self.tool, self.args)


@dataclass(frozen=True)
class Decision:
    approved: bool
    approver: str  # who decided; this ends up in the trace
    note: str = ""


class Approver(Protocol):
    def decide(self, request: ApprovalRequest) -> Decision: ...


class ConsoleApprover:
    """Asks whoever is at the terminal. Anything other than y is a no."""

    def __init__(self, name: str | None = None) -> None:
        self.name = name or getpass.getuser()

    def decide(self, request: ApprovalRequest) -> Decision:
        print(f"\n  APPROVAL NEEDED: {request.summary()}")
        if request.customer_said:
            print(f"  The customer said: \"{request.customer_said}\"")
        print(f"  (conversation bound to {request.customer_id}, release {request.release})")
        try:
            answer = input("  Approve? [y/N] ").strip().lower()
        except EOFError:
            answer = ""
        print()
        return Decision(answer in ("y", "yes"), approver=f"console:{self.name}")


class AutoApprover:
    """Gives the same answer every time and keeps every request. For tests and scripted runs."""

    def __init__(self, approve: bool, name: str = "auto-approver") -> None:
        self.approve = approve
        self.name = name
        self.requests: list[ApprovalRequest] = []

    def decide(self, request: ApprovalRequest) -> Decision:
        self.requests.append(request)
        return Decision(self.approve, approver=self.name, note="automatic")
