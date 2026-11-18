#!/usr/bin/env python3
"""Standalone zero-install EVLOP runner for external agent workspaces."""

from __future__ import annotations

from pathlib import Path
import sys

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE / "vendor"))

from evlop.cli import entry_point  # noqa: E402

if __name__ == "__main__":
    entry_point()
