"""Wires the pieces together according to controls.toml. Used by chat.py, release.py and the tests."""

from __future__ import annotations

from pathlib import Path

from .agent import SupportAgent, Watcher
from .config import InPlaceConfig
from .controls.approvals import Approver
from .controls.rollback import ReleaseHistory
from .db import CustomerDB
from .model import Model, ScriptedModel
from .settings import RELEASES_DIR, STATE_DIR, TRACES_DIR, Controls

FIRST_RELEASE = "v1"


def open_releases(
    controls: Controls, state_dir: Path = STATE_DIR, releases_dir: Path = RELEASES_DIR
) -> InPlaceConfig | ReleaseHistory:
    """The starter overwrites config in place; with the rollback control on, every release is kept."""
    store_type = ReleaseHistory if controls.rollback else InPlaceConfig
    store = store_type(state_dir, releases_dir)
    if not store.has_live():
        store.deploy(FIRST_RELEASE)
    return store


def build_agent(
    controls: Controls,
    approver: Approver,
    *,
    model: Model | None = None,
    db: CustomerDB | None = None,
    state_dir: Path = STATE_DIR,
    traces_dir: Path = TRACES_DIR,
    watch: Watcher | None = None,
) -> SupportAgent:
    return SupportAgent(
        model=model if model is not None else ScriptedModel(),
        db=db if db is not None else CustomerDB(),
        releases=open_releases(controls, state_dir),
        controls=controls,
        approver=approver,
        traces_dir=traces_dir,
        watch=watch,
    )
