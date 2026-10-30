"""Where things live, and which controls are switched on."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, fields
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTROLS_FILE = ROOT / "controls.toml"
RELEASES_DIR = ROOT / "releases"
STATE_DIR = ROOT / ".state"
TRACES_DIR = ROOT / "traces"


@dataclass(frozen=True)
class Controls:
    approvals: bool = False      # Lab 1
    scoped_access: bool = False  # Lab 2
    traces: bool = False         # Lab 3
    rollback: bool = False       # Lab 4

    @classmethod
    def load(cls, mode: str = "file", path: Path = CONTROLS_FILE) -> Controls:
        """mode "file" reads controls.toml; "on" and "off" ignore it and force every control."""
        names = [f.name for f in fields(cls)]
        if mode == "on":
            return cls(**{name: True for name in names})
        if mode == "off":
            return cls()
        if mode != "file":
            raise ValueError(f"mode must be file, on or off, not {mode!r}")

        with open(path, "rb") as f:
            data = tomllib.load(f)
        unknown = set(data) - set(names)
        if unknown:
            raise ValueError(f"{path.name}: unknown control(s) {sorted(unknown)}; expected {names}")
        for name, value in data.items():
            if not isinstance(value, bool):
                raise ValueError(f"{path.name}: {name} must be true or false, not {value!r}")
        return cls(**data)

    def describe(self) -> str:
        return " · ".join(f"{f.name} {'ON' if getattr(self, f.name) else 'off'}" for f in fields(self))
