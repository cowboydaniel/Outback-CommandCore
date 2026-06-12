#!/usr/bin/env python3
"""Compatibility launcher for the PC-X application.

Historically PC-X was launched through ``PC-X/pc_tools_linux.py``.  The
application now lives in ``PC-X/app/main.py``, but keeping this lightweight
wrapper preserves the documented command and any external shortcuts that still
call the old entry point.
"""

from __future__ import annotations

import runpy
from pathlib import Path


APP_ENTRYPOINT = Path(__file__).resolve().parent / "app" / "main.py"


def main() -> None:
    """Run the current PC-X GUI entry point as a script."""
    runpy.run_path(str(APP_ENTRYPOINT), run_name="__main__")


if __name__ == "__main__":
    main()
