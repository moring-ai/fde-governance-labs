"""Lab 3: every tool call is written down, with its input, output, approver and release."""

import pytest

import replay
from bankagent.controls.traces import read_run, render_run
from bankagent.settings import ROOT


def tool_calls(lab) -> list[dict]:
    return [e for e in lab.trace_events() if e["event"] == "tool_call"]


@pytest.mark.control("traces")
def test_every_tool_call_is_traced(lab):
    lab.ask("C-1001", "What's my balance?")
    lab.ask("C-1001", "Please refund the $40 late fee.")

    calls = tool_calls(lab)
    assert [c["tool"] for c in calls] == ["lookup_account", "issue_refund"]
    refund = calls[1]
    assert refund["customer_id"] == "C-1001"
    assert refund["input"] == {"customer_id": "C-1001", "amount": 40, "reason": "Please refund the $40 late fee."}
    assert refund["output"]["data"]["refunded"] == "40.00"
    assert refund["irreversible"] is True
    assert refund["release"] == "v1"
    assert refund["release_hash"] == lab.releases.live().hash


@pytest.mark.control("traces", "approvals")
def test_trace_names_the_approver(lab):
    lab.human.approve = False

    lab.ask("C-1003", "Please close my account.")

    [call] = tool_calls(lab)
    assert call["approval"] == {"approver": "test-approver", "approved": False, "note": "automatic"}
    assert call["output"]["error"] == "not_approved"


@pytest.mark.control("traces")
def test_replay_walks_through_a_run_step_by_step(lab):
    lab.ask("C-1001", "What's my balance?")

    [path] = lab.trace_files()
    header, steps = render_run(read_run(path))
    assert "customer C-1001" in header
    kinds = [step.splitlines()[1].split(":")[0].strip() for step in steps]
    assert kinds == ["customer", "tool", "agent"]


def test_replay_script_reads_the_recorded_example(capsys):
    assert replay.main([str(ROOT / "examples" / "refund-incident.jsonl")]) == 0

    out = capsys.readouterr().out
    assert "issue_refund" in out
    assert "release v2" in out
