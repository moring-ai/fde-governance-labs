"""The agent's three tools: look up an account, issue a refund, close an account.

Each tool gets the database, its own config from the live release (description,
limits), and the arguments the model chose.

Whether a tool is irreversible is a fact about what the tool does, so it is set
here in code, not in release config that ships alongside a prompt edit.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Callable

from .config import Release
from .db import CustomerDB, UnknownCustomer, dollars


class ToolError(Exception):
    pass


def lookup_account(db: CustomerDB, config: dict, customer_id: str) -> dict:
    c = db.get(customer_id)
    return {
        "customer_id": c.customer_id,
        "name": c.name,
        "nickname": c.nickname,
        "email": c.email,
        "balance": dollars(c.balance_cents),
        "status": c.status,
    }


def issue_refund(db: CustomerDB, config: dict, customer_id: str, amount: float, reason: str = "") -> dict:
    cents = to_cents(amount)
    limit = config["max_amount"]
    if cents > limit * 100:
        raise ToolError(f"refunds are limited to ${limit:,}")
    if db.get(customer_id).status != "open":
        raise ToolError(f"account {customer_id} is closed")
    c = db.credit(customer_id, cents)
    return {"customer_id": customer_id, "refunded": dollars(cents), "new_balance": dollars(c.balance_cents)}


def close_account(db: CustomerDB, config: dict, customer_id: str) -> dict:
    if db.get(customer_id).status == "closed":
        raise ToolError(f"account {customer_id} is already closed")
    c = db.close(customer_id)
    return {"customer_id": c.customer_id, "status": c.status}


def to_cents(amount) -> int:
    try:
        cents = int((Decimal(str(amount)) * 100).to_integral_value())
    except InvalidOperation:
        raise ToolError(f"amount {amount!r} is not a number") from None
    if cents <= 0:
        raise ToolError("amount must be more than zero")
    return cents


@dataclass(frozen=True)
class Tool:
    name: str
    fn: Callable[..., dict]
    irreversible: bool
    parameters: dict  # JSON schema for the arguments, as a model would see it


_CUSTOMER_ID = {"type": "string", "description": "Customer id, e.g. C-1001"}

TOOLS = {
    t.name: t
    for t in [
        Tool(
            "lookup_account",
            lookup_account,
            irreversible=False,
            parameters={
                "type": "object",
                "properties": {"customer_id": _CUSTOMER_ID},
                "required": ["customer_id"],
            },
        ),
        Tool(
            "issue_refund",
            issue_refund,
            irreversible=True,
            parameters={
                "type": "object",
                "properties": {
                    "customer_id": _CUSTOMER_ID,
                    "amount": {"type": "number", "description": "Dollars"},
                    "reason": {"type": "string"},
                },
                "required": ["customer_id", "amount"],
            },
        ),
        Tool(
            "close_account",
            close_account,
            irreversible=True,
            parameters={
                "type": "object",
                "properties": {"customer_id": _CUSTOMER_ID},
                "required": ["customer_id"],
            },
        ),
    ]
}


def schemas(release: Release) -> list[dict]:
    """The tool list as the model sees it: name, description and argument schema."""
    out = []
    for name, config in release.tools.items():
        params = copy.deepcopy(TOOLS[name].parameters)
        if "max_amount" in config:
            params["properties"]["amount"]["maximum"] = config["max_amount"]
        out.append({"name": name, "description": config["description"], "parameters": params})
    return out


def run_tool(tool: Tool, db: CustomerDB, release: Release, args: dict) -> dict:
    """Run one tool. Returns {"ok": True, "data": ...} or {"ok": False, "error": ..., "message": ...}."""
    if tool.name not in release.tools:
        return refused("unknown_tool", f"{tool.name} is not part of release {release.version}")
    allowed = tool.parameters["properties"]
    missing = [p for p in tool.parameters["required"] if p not in args]
    extra = [a for a in args if a not in allowed]
    if missing or extra:
        return refused("bad_arguments", f"missing {missing}, unexpected {extra}")
    try:
        return {"ok": True, "data": tool.fn(db, release.tools[tool.name], **args)}
    except (ToolError, UnknownCustomer) as e:
        return refused("tool_error", str(e))


def refused(error: str, message: str) -> dict:
    return {"ok": False, "error": error, "message": message}


def describe(name: str, args: dict) -> str:
    """One line a human approver can read."""
    customer = args.get("customer_id", "?")
    if name == "issue_refund":
        try:
            amount = f"${dollars(to_cents(args.get('amount')))}"
        except ToolError:
            amount = repr(args.get("amount"))
        reason = f" (reason: {args['reason']})" if args.get("reason") else ""
        return f"Refund {amount} to {customer}{reason}"
    if name == "close_account":
        return f"Close account {customer}"
    return f"{name} {json.dumps(args)}"
