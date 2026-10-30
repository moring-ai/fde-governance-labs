"""Lab 4: keep every release, roll back in one command, switch off one tool.

All state lives in one JSON file:

    deployed  stack of release snapshots; the last one is live
    disabled  tools switched off by the kill switch
    log       who did what, and when

A snapshot holds the full prompt and tool config, so a rollback restores exactly
what ran before, even if someone has edited the files in releases/ since.

The agent reads this file on every turn and on every tool call. That is why the
kill switch and rollback take effect in a running agent without a restart.
"""

from __future__ import annotations

import getpass
import json
from datetime import datetime, timezone
from pathlib import Path

from ..config import Release, RollbackUnavailable, load_release, write_json
from ..settings import RELEASES_DIR


class ReleaseHistory:
    def __init__(self, state_dir: Path, releases_dir: Path = RELEASES_DIR) -> None:
        self.path = state_dir / "release_history.json"
        self.releases_dir = releases_dir

    def has_live(self) -> bool:
        return bool(self._load()["deployed"])

    def live(self) -> Release:
        return Release.from_dict(self._load()["deployed"][-1])

    def history(self) -> list[str]:
        return [r["version"] for r in self._load()["deployed"]]

    def log(self) -> list[dict]:
        return self._load()["log"]

    def deploy(self, version: str) -> Release:
        release = load_release(version, self.releases_dir)
        state = self._load()
        state["deployed"].append(release.to_dict())
        self._save(state, "deploy", f"{version} ({release.hash})")
        return release

    def rollback(self) -> Release:
        state = self._load()
        if len(state["deployed"]) < 2:
            raise RollbackUnavailable("Only one release has been deployed. There is nothing earlier to go back to.")
        bad = state["deployed"].pop()
        good = state["deployed"][-1]
        self._save(state, "rollback", f"{bad['version']} -> {good['version']}")
        return Release.from_dict(good)

    def disabled_tools(self) -> set[str]:
        return set(self._load()["disabled"])

    def disable(self, tool: str) -> None:
        if tool not in self.live().tools:
            raise ValueError(f"no tool {tool!r} in the live release")
        state = self._load()
        state["disabled"] = sorted(set(state["disabled"]) | {tool})
        self._save(state, "disable", tool)

    def enable(self, tool: str) -> None:
        state = self._load()
        state["disabled"] = sorted(set(state["disabled"]) - {tool})
        self._save(state, "enable", tool)

    def _load(self) -> dict:
        if not self.path.exists():
            return {"deployed": [], "disabled": [], "log": []}
        return json.loads(self.path.read_text())

    def _save(self, state: dict, action: str, detail: str) -> None:
        state["log"].append({
            "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "by": getpass.getuser(),
            "action": action,
            "detail": detail,
        })
        write_json(self.path, state)
