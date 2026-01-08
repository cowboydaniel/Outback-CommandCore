"""Tests for the CommandCore app entry point."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest


def _ensure_commandcore_on_path() -> None:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def test_main_module_exports_entrypoints() -> None:
    pytest.importorskip("PySide6")
    _ensure_commandcore_on_path()

    if "--skip-deps" not in sys.argv:
        sys.argv.append("--skip-deps")

    module = importlib.import_module("app.main")

    assert hasattr(module, "CommandCoreLauncher")
    assert hasattr(module, "show_splash_screen")
    assert callable(module.main)
