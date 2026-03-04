#!/usr/bin/env python3
"""Launch the Tkinter desktop app."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ddcc_v2.gui import launch_app  # noqa: E402


if __name__ == "__main__":
    launch_app()
