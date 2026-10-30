"""The support agent: a conversation loop, and one place where every tool call is checked.

Read _guarded_call() first. Each switched-on control gets a chance to stop the
call, in this order:

    kill switch     (Lab 4)  is this tool switched off right now?
    scoped access   (Lab 2)  is it about the customer in this conversation?
    approval        (Lab 1)  is it irreversible? then a human says yes or no
    run the tool

_call_tool() wraps it and writes the trace (Lab 3), whatever happened.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .config import InPlaceConfig, Release
from .controls.approvals import ApprovalRequest, Approver, Decision
from .controls.rollback import ReleaseHistory
from .controls.scope import in_scope
from .controls.traces import NoTrace, TraceFile, new_run_id
from .db import CustomerDB
from .model import Model, ToolCall
from .settings import Controls
from .tools import TOOLS, refused, run_tool, schemas

MAX_STEPS = 5

# Called after every tool call with (call, result, decision). chat.py uses it to show tool activity.
Watcher = Callable[[ToolCall, dict, Decision | None], None]


@dataclass
class Conversation:
    customer_id: str  # bound when the conversation starts; nothing in the chat can change it
    run_id: str
    trace: TraceFile | NoTrace
    messages: list[dict] = field(default_factory=list)


class SupportAgent:
    def __init__(
        self,
        *,
        model: Model,
        db: CustomerDB,
        releases: InPlaceConfig | ReleaseHistory,
        controls: Controls,
        approver: Approver,
        traces_dir: Path,
        watch: Watcher | None = None,
    ) -> None:
        self.model = model
        self.db = db
        self.releases = releases
        self.controls = controls
        self.approver = approver
        self.traces_dir = traces_dir
        self.watch = watch

    def start(self, customer_id: str) -> Conversation:
        """Start a conversation for a signed-in customer."""
        run_id = new_run_id()
        trace = (
            TraceFile(self.traces_dir / f"{run_id}.jsonl", run_id, customer_id)
            if self.controls.traces
            else NoTrace()
        )
        return Conversation(customer_id, run_id, trace)

    def send(self, convo: Conversation, text: str) -> str:
        """Handle one customer message and return the agent's reply."""
        release = self.releases.live()  # read every turn, so a deploy or rollback applies at once
        prompt = release.prompt.replace("{customer_id}", convo.customer_id)
        tool_schemas = schemas(release)

        convo.messages.append({"role": "user", "content": text})
        convo.trace.write("user_message", release, text=text)

        for _ in range(MAX_STEPS):
            turn = self.model.respond(prompt, tool_schemas, convo.messages)
            if turn.tool_call is None:
                reply = turn.text or ""
                break
            call = turn.tool_call
            convo.messages.append({"role": "assistant", "tool_call": {"id": call.id, "name": call.name, "args": call.args}})
            result = self._call_tool(convo, release, call)
            convo.messages.append({"role": "tool", "tool_call_id": call.id, "name": call.name, "content": result})
        else:
            reply = "Sorry, I couldn't finish that. A colleague will follow up."

        convo.messages.append({"role": "assistant", "content": reply})
        convo.trace.write("agent_reply", release, text=reply)
        return reply

    def _call_tool(self, convo: Conversation, release: Release, call: ToolCall) -> dict:
        result, decision = self._guarded_call(convo, release, call)
        tool = TOOLS.get(call.name)
        convo.trace.write(
            "tool_call",
            release,
            tool=call.name,
            input=call.args,
            irreversible=bool(tool and tool.irreversible),
            approval=None if decision is None else {
                "approver": decision.approver,
                "approved": decision.approved,
                "note": decision.note,
            },
            output=result,
        )
        if self.watch:
            self.watch(call, result, decision)
        return result

    def _guarded_call(self, convo: Conversation, release: Release, call: ToolCall) -> tuple[dict, Decision | None]:
        tool = TOOLS.get(call.name)
        if tool is None:
            return refused("unknown_tool", f"there is no tool called {call.name}"), None

        if self.controls.rollback and call.name in self.releases.disabled_tools():
            return refused("tool_disabled", f"{call.name} is switched off by the kill switch"), None

        if self.controls.scoped_access and not in_scope(call.args, convo.customer_id):
            return refused("out_of_scope", f"this conversation is bound to {convo.customer_id}"), None

        decision = None
        if self.controls.approvals and tool.irreversible:
            said = next((m["content"] for m in reversed(convo.messages) if m["role"] == "user"), "")
            decision = self.approver.decide(
                ApprovalRequest(call.name, call.args, convo.customer_id, release.version, customer_said=said)
            )
            if not decision.approved:
                return refused("not_approved", f"{decision.approver} did not approve"), decision

        return run_tool(tool, self.db, release, call.args), decision
