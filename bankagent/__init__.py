"""A support agent for a made-up bank, plus the controls that get it through review."""

import sys

if sys.version_info < (3, 11):
    raise SystemExit(
        f"These labs need Python 3.11 or newer; this is {sys.version.split()[0]}. "
        "See Setup in README.md."
    )
