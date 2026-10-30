"""The model interface, and a scripted stand-in so everything runs offline.

The agent only ever calls Model.respond(). To use a real model, write a class
with that one method that sends the same three things to your provider (system
prompt, tool schemas, messages) and maps its answer back to a ModelTurn.
See "Swapping in a real model" in README.md.

Messages are plain dicts:
    {"role": "user", "content": "What's my balance?"}
    {"role": "assistant", "tool_call": {"id": ..., "name": ..., "args": {...}}}
    {"role": "tool", "tool_call_id": ..., "name": ..., "content": {"ok": True, "data": {...}}}
    {"role": "assistant", "content": "Your balance is ..."}
"""

from __future__ import annotations

import itertools
import re
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    args: dict


@dataclass(frozen=True)
class ModelTurn:
    """Either a reply for the customer (text) or one tool to call (tool_call)."""

    text: str | None = None
    tool_call: ToolCall | None = None


class Model(Protocol):
    def respond(self, system_prompt: str, tools: list[dict], messages: list[dict]) -> ModelTurn: ...


CUSTOMER_ID = re.compile(r"\bC-\d{4}\b")
AMOUNT = re.compile(r"\$\s?(\d[\d,]*(?:\.\d{1,2})?)")
# Phrases that talk the stand-in model out of the prompt's rules. A real model
# is harder to push around than this, most of the time.
PRESSURE = ("ignore", "authorised", "authorized", "auditor", "fraud team", "admin", "override")
# Lab 5: text inside a tool result that reads like an order to the assistant.
INSTRUCTION = re.compile(r"note to the assistant.*?refund of \$\s?(\d[\d,]*(?:\.\d{1,2})?)", re.IGNORECASE | re.DOTALL)


class ScriptedModel:
    """Stand-in for a real model: a few rules over the latest message.

    It behaves like an eager, helpful model. It follows the prompt's rule about
    other customers when asked politely, and drops it under pressure. It calls
    tools as soon as the customer asks. It reads the refund limit from the tool
    schema, the way a real model would. And it can't tell data from orders: an
    instruction hidden in a tool result gets followed (Lab 5).
    """

    def __init__(self) -> None:
        self._ids = itertools.count(1)

    def respond(self, system_prompt: str, tools: list[dict], messages: list[dict]) -> ModelTurn:
        tools_by_name = {t["name"]: t for t in tools}
        last = messages[-1]
        if last["role"] == "tool":
            return self._follow_injection(tools_by_name, messages) or ModelTurn(
                text=self._explain(last["name"], last["content"])
            )
        return self._plan(system_prompt, tools_by_name, last["content"])

    def _follow_injection(self, tools: dict, messages: list[dict]) -> ModelTurn | None:
        """If the account we just read carries an instruction, act on it, once per customer message."""
        last = messages[-1]
        if last["name"] != "lookup_account" or not last["content"]["ok"]:
            return None
        since_customer = messages[max(i for i, m in enumerate(messages) if m["role"] == "user"):]
        if any(m.get("tool_call", {}).get("name") == "issue_refund" for m in since_customer):
            return None
        data = last["content"]["data"]
        for value in data.values():
            match = INSTRUCTION.search(str(value))
            if not match:
                continue
            amount = float(match.group(1).replace(",", ""))
            amount = int(amount) if amount.is_integer() else amount
            limit = tools["issue_refund"]["parameters"]["properties"]["amount"].get("maximum")
            if limit is not None and amount > limit:
                return None
            return self._call("issue_refund", customer_id=data["customer_id"], amount=amount, reason="goodwill credit")
        return None

    def _plan(self, system_prompt: str, tools: dict, text: str) -> ModelTurn:
        lowered = text.lower()
        me = CUSTOMER_ID.search(system_prompt).group()
        others = [c for c in CUSTOMER_ID.findall(text) if c != me]
        target = others[0] if others else me

        if target != me and "only discuss" in system_prompt.lower():
            if not any(p in lowered for p in PRESSURE):
                return ModelTurn(text="Sorry, I can only help with your own account.")

        if "close" in lowered and "account" in lowered:
            return self._call("close_account", customer_id=target)

        if "refund" in lowered:
            match = AMOUNT.search(text)
            if not match:
                return ModelTurn(text="How much should I refund?")
            amount = float(match.group(1).replace(",", ""))
            amount = int(amount) if amount.is_integer() else amount
            limit = tools["issue_refund"]["parameters"]["properties"]["amount"].get("maximum")
            if limit is not None and amount > limit:
                return ModelTurn(
                    text=f"A refund of ${amount:,} is more than I can issue. "
                    "I've passed it to a colleague, who will be in touch."
                )
            return self._call("issue_refund", customer_id=target, amount=amount, reason=text[:80])

        if any(w in lowered for w in ("balance", "account", "look up", "details")):
            return self._call("lookup_account", customer_id=target)

        return ModelTurn(text="I can look up your account, issue a refund, or close your account.")

    def _call(self, name: str, **args) -> ModelTurn:
        return ModelTurn(tool_call=ToolCall(f"call-{next(self._ids)}", name, args))

    def _explain(self, tool: str, result: dict) -> str:
        if not result["ok"]:
            return {
                "not_approved": "That needs sign-off from a colleague, and it wasn't approved, "
                "so nothing has changed.",
                "out_of_scope": "Sorry, I can only help with the account you're signed in with.",
                "tool_disabled": "I can't do that right now. I've passed your request to a colleague.",
            }.get(result["error"], f"Sorry, that didn't work: {result['message']}.")
        d = result["data"]
        if tool == "lookup_account":
            return (
                f"Account {d['customer_id']}, {d['name']} ({d['email']}): "
                f"balance ${d['balance']}, status {d['status']}."
            )
        if tool == "issue_refund":
            return f"Done. I've refunded ${d['refunded']}. The new balance is ${d['new_balance']}."
        if tool == "close_account":
            return f"Account {d['customer_id']} is now closed."
        return f"Done: {d}"
