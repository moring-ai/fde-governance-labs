"""Shared test setup.

Each test gets a Lab: a fresh bank database, an agent wired according to
controls.toml (or --controls=on/off), and an approver that stands in for the
human. State and traces go to a temp folder, never to the repo's .state/ or
traces/.

Tests marked @pytest.mark.control("name") check how a control behaves, so they
are skipped until that control is on. The three failure tests are not marked:
they run every time, and fail until their control is on.
"""

from __future__ import annotations

import pytest

from bankagent.agent import SupportAgent
from bankagent.app import open_releases
from bankagent.controls.approvals import AutoApprover
from bankagent.controls.traces import read_run
from bankagent.db import CustomerDB
from bankagent.model import ScriptedModel
from bankagent.settings import Controls


def pytest_addoption(parser):
    parser.addoption(
        "--controls",
        choices=["file", "on", "off"],
        default="file",
        help="file: read controls.toml (default); on/off: force every control on or off",
    )


def _controls(config) -> Controls:
    return Controls.load(config.getoption("controls"))


def pytest_report_header(config):
    return f"controls: {_controls(config).describe()}"


def pytest_runtest_setup(item):
    marker = item.get_closest_marker("control")
    if marker:
        controls = _controls(item.config)
        off = [name for name in marker.args if not getattr(controls, name)]
        if off:
            pytest.skip(f"turn on {' and '.join(off)} in controls.toml")


class Lab:
    def __init__(self, controls: Controls, tmp_path) -> None:
        self.controls = controls
        self.db = CustomerDB()
        # The human approver. Says yes unless a test sets human.approve = False.
        self.human = AutoApprover(approve=True, name="test-approver")
        self.releases = open_releases(controls, tmp_path / "state")
        self.traces_dir = tmp_path / "traces"
        self.agent = SupportAgent(
            model=ScriptedModel(),
            db=self.db,
            releases=self.releases,
            controls=controls,
            approver=self.human,
            traces_dir=self.traces_dir,
        )
        self.conversations = []

    def ask(self, customer_id: str, text: str) -> str:
        """Start a new conversation as customer_id, send one message, return the reply."""
        convo = self.agent.start(customer_id)
        self.conversations.append(convo)
        return self.agent.send(convo, text)

    def balance(self, customer_id: str) -> int:
        return self.db.get(customer_id).balance_cents

    def status(self, customer_id: str) -> str:
        return self.db.get(customer_id).status

    def trace_files(self):
        """One trace file per conversation, in the order the conversations happened."""
        return [c.trace.path for c in self.conversations if c.trace.path and c.trace.path.exists()]

    def trace_events(self) -> list[dict]:
        return [e for path in self.trace_files() for e in read_run(path)]


@pytest.fixture
def lab(request, tmp_path) -> Lab:
    return Lab(_controls(request.config), tmp_path)
