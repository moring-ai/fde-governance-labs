"""Releases: a versioned prompt plus tool config, and how the starter ships them.

A release is a folder under releases/ holding prompt.txt and tools.json.
The folder name is the version.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

from .settings import RELEASES_DIR


class RollbackUnavailable(RuntimeError):
    pass


class KillSwitchUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class Release:
    version: str
    prompt: str
    tools: dict[str, dict]

    @property
    def hash(self) -> str:
        """Fingerprint of exactly what ran. Changes if one character of prompt or config changes."""
        body = self.prompt + json.dumps(self.tools, sort_keys=True)
        return hashlib.sha256(body.encode()).hexdigest()[:12]

    def to_dict(self) -> dict:
        return {"version": self.version, "prompt": self.prompt, "tools": self.tools}

    @classmethod
    def from_dict(cls, data: dict) -> Release:
        return cls(data["version"], data["prompt"], data["tools"])


def load_release(version: str, releases_dir: Path = RELEASES_DIR) -> Release:
    folder = releases_dir / version
    if not folder.is_dir():
        available = sorted(p.name for p in releases_dir.iterdir() if p.is_dir())
        raise ValueError(f"no release {version!r}; available: {', '.join(available)}")
    prompt = (folder / "prompt.txt").read_text()
    tools = json.loads((folder / "tools.json").read_text())
    return Release(version, prompt, tools)


def write_json(path: Path, data: dict) -> None:
    """Write via a temp file so a reader in another process never sees half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(tmp, path)


class InPlaceConfig:
    """How the starter ships a change: overwrite the live prompt and tool config.

    There is one slot. Deploying v2 replaces v1, and nothing remembers that v1
    was ever live. No rollback, no kill switch.
    """

    def __init__(self, state_dir: Path, releases_dir: Path = RELEASES_DIR) -> None:
        self.path = state_dir / "live_config.json"
        self.releases_dir = releases_dir

    def has_live(self) -> bool:
        return self.path.exists()

    def live(self) -> Release:
        return Release.from_dict(json.loads(self.path.read_text()))

    def deploy(self, version: str) -> Release:
        release = load_release(version, self.releases_dir)
        write_json(self.path, release.to_dict())
        return release

    def rollback(self) -> Release:
        raise RollbackUnavailable(
            "Nothing to roll back to. The starter overwrites the live prompt and tool "
            "config in place, so the previous version is gone. "
            "(Lab 4: set rollback = true in controls.toml.)"
        )

    def disabled_tools(self) -> set[str]:
        return set()

    def disable(self, tool: str) -> None:
        raise KillSwitchUnavailable(
            "The starter has no kill switch. To stop a tool you would edit tools.json and "
            "redeploy. (Lab 4: set rollback = true in controls.toml.)"
        )

    def enable(self, tool: str) -> None:
        raise KillSwitchUnavailable("The starter has no kill switch. (Lab 4: set rollback = true in controls.toml.)")
